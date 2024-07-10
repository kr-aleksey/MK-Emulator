import asyncio


class MKScales:
    HEADER_SLICE = slice(0, 3)
    LEN_SLICE = slice(3, 5)
    BODY_START = 5

    def __init__(self):
        # Заголовок пакетов запроса и ответа
        self.packet_header = b'\xF8\x55\xCE'
        # Команда запроса: обработчик
        self._commands = {
            b'\xA0': self.get_weight,
            b'\x90': self.get_id
        }

    def get_weight(self):
        command = b'\x10'
        weight = b'\x00\x00\x00\x00'
        division = b'\x03'
        return command + weight + division

    def get_id(self):
        command = b'\x50'
        serial = b'1234'
        return command + serial

    @staticmethod
    def calc_crc(data: bytes | bytearray) -> bytes:
        poly = 0x1021
        # crc = 0xffff
        crc = 0
        for byte in data:
            for _ in range(8):
                if (byte ^ (crc >> 8)) & 0x80:
                    crc <<= 1
                    crc ^= poly
                else:
                    crc <<= 1
                byte <<= 1
                byte &= 0xff
                crc &= 0xffff

        crc = hex(crc)
        return crc

    def check_request(self, request: bytes) -> bytes:
        header = request[self.HEADER_SLICE]
        if header != self.packet_header:
            raise ValueError(f'Неверный заголовок запроса. '
                             f'Ожидалось: {self.packet_header}. '
                             f'Получено: {header}')
        data_len = int.from_bytes(request[self.LEN_SLICE])
        body_end = self.BODY_START + data_len
        request_body = request[self.BODY_START: body_end]
        received_crc = request[body_end: body_end + 2]
        computed_crc = self.calc_crc(request_body)

        if received_crc != computed_crc:
            raise ValueError(f'Неверный CRC запроса. '
                             f'Вычисленное значение: {computed_crc}. '
                             f'Получено: {received_crc}')
        return request_body

    def wrap_data(self, data: bytes | bytearray) -> bytes:
        crc = self.calc_crc(data)
        data_len = len(data).to_bytes()
        return self.packet_header + data_len + data + crc

    def exec_command(self, request: bytes | bytearray) -> bytes:
        """Обработчик команды. Принимает команду,
        возвращает результат ее выполнения."""

        request = self.check_request(request)
        data = self._commands[request[0:1]]()
        return self.wrap_data(data)

    async def request_handler(self, reader, writer):
        request = await reader.read(100)
        addr = writer.get_extra_info('peername')
        print(f'Client {addr}, request: {request!r}')
        response = self.exec_command(request)
        print(f'Response: {request.decode()}')
        writer.write(response)
        await writer.drain()
        print('Close')
        writer.close()
        await writer.wait_closed()


async def main():
    d = MKScales()
    server = await asyncio.start_server(d.request_handler, None, 8000)
    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
