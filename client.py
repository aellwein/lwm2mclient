#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiocoap import resource
from aiocoap.message import Message
from aiocoap.numbers.codes import Code
from aiocoap.protocol import Context
from aiocoap.resource import ObservableResource

from encdec import PayloadEncoder
from handlers import *
from model import ClientModel

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("client")


class RequestHandler(ObservableResource):
    def __init__(self, model, encoder):
        super(RequestHandler, self).__init__()
        self.model = model
        self.encoder = encoder

    def handle_read(self, path):
        return self.encoder.encode(path)

    def handle_observe(self, request):
        path = request.opt.uri_path
        l = len(path)
        if l == 1:
            obs = "observe_%s" % path[0]
        elif l == 2:
            obs = "observe_%s_%s" % (path[0], path[1])
        elif l == 3:
            obs = "observe_%s_%s_%s" % (path[0], path[1], path[2])
        else:
            return Message(code=Code.BAD_REQUEST)

        def _notifier():
            self.updated_state(response=self.encoder.encode(path))

        try:
            obs_method = eval(obs)
            cancel = request.opt.observe == "0"
            _kwargs = dict(model=self.model, path=path, payload=request.payload,
                           content_format=request.opt.content_format, cancel=cancel, notifier=_notifier)
            obs_method(None, **_kwargs)
            return self.encoder.encode(path)
        except NameError:
            pass
        return Message(code=Code.METHOD_NOT_ALLOWED)

    def handle_exec(self, request):
        path = request.opt.uri_path
        if len(path) != 3 or not self.model.is_path_valid(path):
            return Message(code=Code.BAD_REQUEST)
        if not self.model.is_resource_executable(path[0], path[1], path[2]):
            return Message(code=Code.METHOD_NOT_ALLOWED)
        _op = str(self.model.resource(path[0], path[1], path[2]))
        try:
            _op_method = eval(_op)
        except NameError:
            log.error(
                "handler \"%s\" for %s is not implemented. Please implement it in handlers.py" % (_op, "/".join(path)))
            return Message(code=Code.NOT_IMPLEMENTED)
        _kwargs = dict(model=self.model, payload=request.payload, path=path, content_format=request.opt.content_format)
        result = _op_method(None, **_kwargs)
        return Message(code=Code.CHANGED, payload=result) if result is not None else Message(code=Code.CHANGED)

    @asyncio.coroutine
    def render_get(self, request):
        if request.opt.observe is not None:
            log.debug("observe on %s" % "/".join(request.opt.uri_path))
            return self.handle_observe(request)
        else:
            log.debug("read on %s" % "/".join(request.opt.uri_path))
            return self.handle_read(request.opt.uri_path)

    @asyncio.coroutine
    def render_put(self, request):
        log.debug("write on %s" % "/".join(request.opt.uri_path))
        # TODO: implement write here
        return Message(code=Code.CHANGED)

    @asyncio.coroutine
    def render_post(self, request):
        log.debug("execute on %s" % "/".join(request.opt.uri_path))
        return self.handle_exec(request)


class Client(resource.Site):
    endpoint = "python-client"
    binding_mode = "UQ"
    lifetime = 86400  # default: 86400
    context = None
    rd_resource = None

    def __init__(self, model=ClientModel(), server="localhost", server_port=5683):
        super(Client, self).__init__()
        self.server = server
        self.server_port = server_port
        self.model = model
        self.encoder = PayloadEncoder(model)
        self.request_handler = RequestHandler(self.model, self.encoder)
        for path in model.instance_iter():
            self.add_resource(path, self.request_handler)
        for path in model.resource_iter():
            self.add_resource(path, self.request_handler)

    @asyncio.coroutine
    def update_register(self):
        log.debug("update_register()")
        update = Message(code=Code.POST)
        update.opt.uri_host = self.server
        update.opt.uri_port = self.server_port
        update.opt.uri_path = ("rd", self.rd_resource)
        response = yield from self.context.request(update).response
        if response.code != Code.CHANGED:
            # error while update, fallback to re-register
            log.warn("failed to update registration, code {}, falling back to registration".format(response.code))
            asyncio.ensure_future(self.run())
        else:
            log.info("updated registration for %s" % self.rd_resource)
            # yield to next update - 1 sec
            yield from asyncio.sleep(self.lifetime - 1)
            asyncio.ensure_future(self.update_register())

    @asyncio.coroutine
    def run(self):
        self.context = yield from Context.create_server_context(self, bind=("::", 0))

        # send POST (registration)
        request = Message(code=Code.POST, payload=",".join(self.model.get_object_links()).encode())
        request.opt.uri_host = self.server
        request.opt.uri_port = self.server_port
        request.opt.uri_path = ("rd",)
        request.opt.uri_query = ("ep=%s" % self.endpoint, "b=%s" % self.binding_mode, "lt=%d" % self.lifetime)
        response = yield from self.context.request(request).response

        # expect ACK
        if response.code != Code.CREATED:
            raise BaseException("unexpected code received: %s. Unable to register!" % response.code)

        # we receive resource path ('rd', 'xyz...')
        self.rd_resource = response.opt.location_path[1].decode()
        log.info("client registered at location %s" % self.rd_resource)
        yield from asyncio.sleep(self.lifetime - 1)
        asyncio.ensure_future(self.update_register())


if __name__ == '__main__':
    client = Client()
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(client.run())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
        exit(0)
