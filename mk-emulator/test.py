import asyncio


async def main():
    reader, writer = await asyncio.open_connection('localhost', 8000)
    print('send request')
    writer.write(b'\xF8\x55\xCE\x00\x01\x90\x4F\x25')
    await writer.drain()
    try:
        response = await asyncio.wait_for(reader.read(100), timeout=2)
        print(response.decode())
    except asyncio.TimeoutError:
        print('нет ответа')
    pass
    # print(response.decode())

if __name__ == '__main__':
    asyncio.run(main())
