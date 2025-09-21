import olma
from tinyllama.main import run_tiny_llama
def main():
    olma.Connect(username="my-api-user", password="my-api-password")
    server = run_tiny_llama()
    start_tiny_llama(server)
if __name__ == '__main__':
    main()

