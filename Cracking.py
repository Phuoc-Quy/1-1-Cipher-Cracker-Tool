import math, random, re


"""Tool to evaluate the english likeliness of a text"""
class Distribution(dict):
    # ------------------------------------------------------------------------------------------------
    # This class act like a dictionary for looking up the probability of a word given the distribution
    # If a word is unknown, we give them a very small probability
    # ------------------------------------------------------------------------------------------------
    def __init__(self, file_name):
        self.count = 0

        with open(file_name, 'r') as file:
            lines = file.readlines()
        file.close()

        for line in lines:
            (word, count) = line[:-1].split('\t')
            self[word] = int(count)
            self.count += int(count)

    def __call__(self, key):
        if key in self:
            return float(self[key]) / self.count
        return 1.0 / (self.count * 10**(len(key)-2))            

def memoize(f):
   # --------------
   # Speed up stuff
   # --------------
   cache = {}
   
   def memoizedFunction(*args):
      if args not in cache:
         cache[args] = f(*args)
      return cache[args]

   memoizedFunction.cache = cache
   return memoizedFunction

@memoize
def create_list_of_words(text):
    # ----------------------------------------------------------------------------
    # Return a list of most possible words from the text based on the distribution
    # ----------------------------------------------------------------------------
    if not text:
        return []
    text = text.lower()
    possible_words = [[first] + create_list_of_words(last) for (first, last) in cut_word(text)]
    return max(possible_words, key=english_score)

def cut_word(word, maximun=20):
   # ---------------------------------------------------------------
   # Return a pair of possible part of the word
   # For example, CAT can be cut in to (C, AT), (CA, T), and (CAT, )
   # There is very few words that has 20 or more letters
   # ---------------------------------------------------------------
   return [(word[:i+1], word[i+1:]) for i in range(max(len(word), maximun))]

words_dictionary = Distribution('words.txt')
def english_score(list_of_words):
    return sum(math.log10(words_dictionary(word)) for word in list_of_words)

def get_result(text):
    # ---------------------------------------
    # Return the list of words with its score
    # ---------------------------------------
    list_of_words = create_list_of_words(text)
    return (english_score(list_of_words), list_of_words)


"""Cracking the cypher tool"""
alphabet = 'abcdefghijklmnopqrstuvwxyz'

def translate(text, key):
    # ------------------------------
    # Translate the text using a key
    # ------------------------------
    v_a = ord('a')
    v_z = ord('z')
    v_A = ord('A')
    v_Z = ord('Z')
    new_text = ''
    for letter in text:
        v_letter = ord(letter)
        if v_a <= v_letter <= v_z: #letter is lowercase
            new_text += key[v_letter-v_a]
        elif v_A <= v_letter <= v_Z: #letter is uppercase
            new_text += key[v_letter-v_A].upper()
        else: #letter is non-alphabet
            new_text += letter
    return new_text

def swap_letter(text, letter1, letter2):
    # -------------------------
    # Swap two letter in a text
    # -------------------------
    new_text = ''
    for letter in text:
        if letter == letter1:
            new_text += letter2
        elif letter == letter2:
            new_text += letter1
        else:
            new_text += letter
    return new_text

def n_gram(text, n):
    # -------------------------------------------
    # Generate a list of n_gram of the given text
    # -------------------------------------------
    return [text[i:i+n] for i in range(len(text) - (n-1))]

def hill_climb_local(text, key, evaluate_function, number_of_steps):
    # --------------------------------
    # Find the text with highest score
    # --------------------------------
    decrypted = translate(text, key)
    score = evaluate_function(decrypted)
    neighbors = iter(generate_neighbor_keys(key, decrypted)) # generate some neighbor key

    for step in range(number_of_steps): # compare this key to other neighbor key
        #print(step)
        next_key = next(neighbors)
        next_decrypted = translate(text, next_key)
        next_score = evaluate_function(next_decrypted)

        if next_score > score: #find better key, swap to higher score key
            key = next_key
            decrypted = next_decrypted
            score = next_score
            neighbors = iter(generate_neighbor_keys(key, decrypted)) # generate more neighbor key for next step
            #print((decrypted, key))
    
    return decrypted

bigram_dictionary = Distribution('2_gram.txt')
def generate_neighbor_keys(key, decrypted):
    # -----------------------------------------------------------------------------
    # Generate neighbor key by changing less frequent bigraph to a more popular one
    # -----------------------------------------------------------------------------
    bigrams = sorted(n_gram(decrypted, 2), key=bigram_dictionary)[:30]

    for letter1, letter2 in bigrams: # get the most less-frequent bigrams
        for letter in randomize(alphabet):
            if letter1 == letter2 and bigram_dictionary(letter+letter) > bigram_dictionary(letter1+letter2): #doublet
                yield swap_letter(key, letter, letter1)
            else: #non-doublet
                # swap to better bigram
                if bigram_dictionary(letter+letter2) > bigram_dictionary(letter1+letter2):
                    yield swap_letter(key, letter, letter1)
                if bigram_dictionary(letter1+letter) > bigram_dictionary(letter1+letter2):
                    yield swap_letter(key, letter, letter2)

    while True: #otherwise, generate a random key
        yield swap_letter(key, random.choice(alphabet), random.choice(alphabet))

def randomize(text):
    text_to_list = list(text)
    random.shuffle(text_to_list)
    return ''.join(text_to_list)

trigram_dictionary = Distribution('3_gram.txt')
def trigram_text_score(text):
    return sum(math.log10(trigram_dictionary(trigram)) for trigram in n_gram(text, 3))

def deduce_key(ciphertext, decrypted):
    """
    Deduce the substitution key given the ciphertext and the decrypted text.
    For each lowercase letter in the ciphertext, assume that the corresponding
    decrypted letter is the mapping. If some letters in the key are left unfilled,
    fill them with the remaining letters that have not been used.
    """
    # Initialize the key with placeholders for 26 letters.
    key = ['?'] * 26
    
    # For each letter in the ciphertext, deduce the mapping if possible.
    for c, d in zip(ciphertext, decrypted):
        if c.islower() and d.islower():
            index = ord(c) - ord('a')
            key[index] = d
    
    # Determine which letters have already been used.
    used_letters = {letter for letter in key if letter != '?'}
    
    # Create a list of remaining letters not yet used.
    remaining_letters = [letter for letter in "abcdefghijklmnopqrstuvwxyz" if letter not in used_letters]
    remaining_letters.sort()  # You can sort them, or shuffle for randomness if preferred.
    
    # Fill in the missing positions in the key.
    for i, letter in enumerate(key):
        if letter == '?':
            key[i] = remaining_letters.pop(0)
    
    return ''.join(key)

def hill_climb(text, number_of_steps=7000, number_of_retry=20):
    # Preprocess the ciphertext
    processed = process_text(text)
    
    # Generate several random starting keys
    initial_keys = [randomize(alphabet) for _ in range(number_of_retry)]
    
    # Run hill_climb_local on each initial key.
    # Each element is a tuple: (initial_key, decrypted_text)
    local_maxes = [
        (key, hill_climb_local(processed, key, trigram_text_score, number_of_steps))
        for key in initial_keys
    ]
    
    # Select the best result based on its evaluation score.
    best_initial_key, best_decrypted = max(local_maxes, key=lambda x: get_result(x[1])[0])
    score, words = get_result(best_decrypted)
    
    # Deduce the final key by comparing the processed ciphertext and the best decryption.
    best_key = deduce_key(processed, best_decrypted)
    
    return ' '.join(words), score, best_key

def process_text(text):
    return ''.join(re.findall('[a-z]+', text.lower()))

"""Analysis tools"""

def sample_run(text, number_of_trial=20):
    for i in range(number_of_trial):
        print(hill_climb(text))

def sample_run_log(file_name, number_of_trial=20):
    with open(file_name, 'r') as infile:
        lines = infile.readlines()
    infile.close()

    for index, line in enumerate(lines, start=1):
        output_filename = f"text{index}.txt"
        with open(output_filename, 'w') as outfile:
            outfile.write(line)
            for i in range(number_of_trial):
                text, score, key = hill_climb(line)
                outfile.write('-----\n')
                outfile.write(text+'\n')
                outfile.write(str(score)+'\n')
                outfile.write(key+'\n')
                outfile.write('-----\n')
        outfile.close()

def main():
    with open('crypto_code.txt', 'r') as infile:
        lines = [line.strip() for line in infile if line.strip()]

    for index, line in enumerate(lines, start=1):
        decrypted_text, score, key = hill_climb(line)
        print(f'Ciphertext {index}: {line}')
        print(f'Decrypted  {index}: {decrypted_text}')
        print(f'Score      {index}: {score}')
        print(f'Key        {index}: {key}')
        print()


if __name__ == '__main__':
    main()