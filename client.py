#!/usr/bin/env python3
import argparse

from aiocoap import error, resource
from aiocoap.message import Message
from aiocoap.numbers.codes import Code
from aiocoap.protocol import Context
from aiocoap.resource import ObservableResource

from encdec import PayloadDecoder, PayloadEncoder
from handlers import *
from model import ClientModel

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger('client')


class RequestHandler(ObservableResource):
    def __init__(self, model, encoder, decoder):
        super(RequestHandler, self).__init__()
        self.model = model
        self.encoder = encoder
        self.decoder = decoder

    def handle_read(self, path):
        return self.encoder.encode(path)

    def handle_write(self, path, payload, content_format):
        return self.decoder.decode(path, payload, content_format)

    def handle_observe(self, path, request):
        plen = len(path)
        if plen == 1:
            obs = f'observe_{path[0]}'
        elif plen == 2:
            obs = f'observe_{path[0]}_{path[1]}'
        elif plen == 3:
            obs = f'observe_{path[0]}_{path[1]}_{path[2]}'
        else:
            return Message(code=Code.BAD_REQUEST)

        def _notifier():
            self.updated_state(response=self.encoder.encode(path))

        try:
            obs_method = eval(obs)
            cancel = request.opt.observe == '0'
            _kwargs = dict(model=self.model,
                           path=path,
                           payload=request.payload,
                           content_format=request.opt.content_format,
                           cancel=cancel,
                           notifier=_notifier)
            obs_method(None, **_kwargs)
            return self.encoder.encode(path)
        except NameError:
            pass
        return Message(code=Code.METHOD_NOT_ALLOWED)

    def handle_exec(self, path, request):
        if len(path) != 3 or not self.model.is_path_valid(path):
            return Message(code=Code.BAD_REQUEST)
        if not self.model.is_resource_executable(path[0], path[1], path[2]):
            return Message(code=Code.METHOD_NOT_ALLOWED)
        _op = str(self.model.resource(path[0], path[1], path[2]))
        try:
            _op_method = eval(_op)
        except NameError:
            log.error(
                f'handler "{_op}" for {"/".join(path)} is not implemented. Please implement it in handlers.py')
            return Message(code=Code.NOT_IMPLEMENTED)
        _kwargs = dict(model=self.model, payload=request.payload,
                       path=path, content_format=request.opt.content_format)
        result = _op_method(None, **_kwargs)
        return Message(code=Code.CHANGED, payload=result) if result is not None else Message(code=Code.CHANGED)

    async def render(self, req):
        path, request = req
        m = getattr(self, 'render_%s' % str(request.code).lower(), None)
        if not m:
            raise error.UnallowedMethod()
        return await m(path, request)

    async def render_get(self, path, request):
        if request.opt.observe is not None:
            log.debug(f'observe on {"/".join(path)}')
            return self.handle_observe(path, request)
        else:
            log.debug(f'read on {"/".join(path)}')
            return self.handle_read(path)

    async def render_put(self, path, request):
        log.debug(f'write on {"/".join(path)}')
        message, _decoded = self.handle_write(
            path, request.payload, request.opt.content_format)
        if message.code == Code.CHANGED:
            self.model.apply(_decoded)
        return message

    async def render_post(self, path, request):
        log.debug(f'execute on {"/".join(path)}')
        return self.handle_exec(path, request)


class Client(resource.Site):
    endpoint = 'python-client'
    binding_mode = 'UQ'
    lifetime = 86400  # default: 86400
    context = None
    rd_resource = None

    def __init__(self, model=ClientModel(), server='localhost', server_port=5683, **kwargs):
        super(Client, self).__init__()
        self.server = server
        self.server_port = server_port
        self.address = kwargs['address'] if 'address' in kwargs else '::'
        self.model = model
        self.encoder = PayloadEncoder(model)
        self.decoder = PayloadDecoder(model)
        self.request_handler = RequestHandler(
            self.model, self.encoder, self.decoder)
        for path in model.instance_iter():
            self.add_resource(path, self.request_handler)
        for path in model.resource_iter():
            self.add_resource(path, self.request_handler)

    async def render(self, request):
        uri_path = request.opt.uri_path
        if len(uri_path) == 0:
            return await super().render(request)
        else:
            return await self.request_handler.render((uri_path, request,))

    async def update_register(self):
        log.debug('update_register()')
        update = Message(code=Code.POST)
        update.opt.uri_host = self.server
        update.opt.uri_port = self.server_port
        update.opt.uri_path = ('rd', self.rd_resource)
        response = await self.context.request(update).response
        if response.code != Code.CHANGED:
            # error while update, fallback to re-register
            log.warning(
                f'failed to update registration, code {response.code}, falling back to registration')
            asyncio.ensure_future(self.run())
        else:
            log.info(f'updated registration for {self.rd_resource}')
            # yield to next update - 1 sec
            await asyncio.sleep(self.lifetime - 1)
            asyncio.ensure_future(self.update_register())

    async def run(self):
        self.context = await Context.create_server_context(self, bind=(self.address, 0))

        # send POST (registration)
        request = Message(code=Code.POST, payload=','.join(
            self.model.get_object_links()).encode())
        request.opt.uri_host = self.server
        request.opt.uri_port = self.server_port
        request.opt.uri_path = ('rd',)
        request.opt.uri_query = (
            f'ep={self.endpoint}', f'b={self.binding_mode}', f'lt={self.lifetime}')
        response = await self.context.request(request).response

        # expect ACK
        if response.code != Code.CREATED:
            raise BaseException(
                f'unexpected code received: {response.code}. Unable to register!')

        # we receive resource path ('rd', 'xyz...')
        self.rd_resource = response.opt.location_path[1]
        log.info(f'client registered at location {self.rd_resource}')
        await asyncio.sleep(self.lifetime - 1)
        asyncio.ensure_future(self.update_register())


if __name__ == '__main__':
    parser = argparse.ArgumentParser('lwm2mclient')
    parser.add_argument('--address', type=str, default='::',
                        help='Address for client to bind and listen for incoming requests')
    args = parser.parse_args()

    client = Client(**vars(args))
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(client.run())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
        exit(0)
