import olma
from tinyllama.main import run_server, start_tiny_llama
def main():
    olma.Connect(username="my-api-user", password="my-api-password")
    server = run_server()
    start_tiny_llama(server)
if __name__ == '__main__':
    main()

