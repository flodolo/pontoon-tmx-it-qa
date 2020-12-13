#!/usr/bin/python3

import hunspell
import os


def main():
    script_path = os.path.abspath(os.path.dirname(__file__))

    # Set up spellcheckers
    # Load hunspell dictionaries
    dictionary_path = os.path.join(
        script_path, os.path.pardir, 'dictionaries')
    spellchecker = hunspell.HunSpell(
        os.path.join(dictionary_path, 'it_IT.dic'),
        os.path.join(dictionary_path, 'it_IT.aff'),
    )

    # Load the extra dictionary as a normal file
    extra_dict = os.path.join(dictionary_path, 'additional_words.dic')
    with open(extra_dict) as f:
        terms = []
        for i, line in enumerate(f):
            line = line.rstrip()
            # Ignore number of items at the beginning
            if i == 0:
                continue

            # Ignore comments and empty lines
            if line == '' or line.startswith('/'):
                continue

            terms.append(line.split('/')[0])

    print(f"Additional terms loaded: {len(terms)}")
    # Check spelling for each term. If it passes, it should be removed
    to_remove = []
    for term in terms:
        if spellchecker.spell(term):
            to_remove.append(term)

    if to_remove:
        print("Terms to remove:")
        print("\n".join(to_remove))


if __name__ == '__main__':
    main()
