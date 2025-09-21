"""Example file to test Tiny Code functionality"""

def fibonacci(n):
    """Calculate the nth Fibonacci number"""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    """Calculate factorial of n"""
    if n < 0:
        raise ValueError("Factorial not defined for negative numbers")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def is_prime(n):
    """Check if a number is prime"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

if __name__ == "__main__":
    print(f"Fibonacci(10): {fibonacci(10)}")
    print(f"Factorial(5): {factorial(5)}")
    print(f"Is 17 prime? {is_prime(17)}")