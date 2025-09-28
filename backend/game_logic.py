def evaluate_guess(secret: str, guess: str):
    """
    Returns list of ['G','O','X'] for green, orange, grey.
    """
    secret = secret.upper()
    guess = guess.upper()
    result = ['X'] * 5
    secret_chars = list(secret)

    # Greens
    for i in range(5):
        if guess[i] == secret_chars[i]:
            result[i] = 'G'
            secret_chars[i] = None

    # Oranges
    for i in range(5):
        if result[i] == 'G':
            continue
        if guess[i] in secret_chars:
            result[i] = 'O'
            idx = secret_chars.index(guess[i])
            secret_chars[idx] = None

    return result
