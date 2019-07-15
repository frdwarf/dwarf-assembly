def slow_fibo(n):
    if n <= 1:
        return 1
    return slow_fibo(n - 1) + slow_fibo(n - 2)


if __name__ == "__main__":
    slow_fibo(35)
