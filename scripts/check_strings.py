#!/usr/bin/python3

from html.parser import HTMLParser
from lxml import etree
import hunspell
import json
import nltk
import os
import re
import string
import sys


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ' '.join(self.fed)


class CheckStrings():

    included_products = (
        'android-l10n',
        'firefox-for-ios',
        'mozillaorg',
        'mozilla-vpn-client',
        'firefox-monitor-website',
    )

    '''
amo
amo-frontend
amo-linter
appstores
common-voice
copyright-campaign
donate-mozilla-content
donate-thunderbird-content
engagement
engagement-heartbeat-apr2018
facebook-container
firefox-accounts
firefox-accounts-payments
firefox-for-fire-tv
firefox-monitor-add-on
fundraising
mdn
mozilla-advocacy
mozilla-donate-website
mozilla-learning-network
seamonkey
sumo
thunderbirdnet
webthings-gateway
'''

    def __init__(self, script_path, tmx_file):
        '''Initialize object'''

        self.verbose = False
        self.tmx_file = tmx_file
        self.translations = {}

        self.script_path = script_path
        self.exceptions_path = os.path.join(
            script_path, os.path.pardir, 'exceptions')
        self.errors_path = os.path.join(
            script_path, os.path.pardir, 'errors')

        # Set up spellcheckers
        # Load hunspell dictionaries
        dictionary_path = os.path.join(
            self.script_path, os.path.pardir, 'dictionaries')
        self.spellchecker = hunspell.HunSpell(
            os.path.join(dictionary_path, 'it_IT.dic'),
            os.path.join(dictionary_path, 'it_IT.aff'),
        )
        self.spellchecker.add_dic(
            os.path.join(dictionary_path, 'mozilla_qa_specialized.dic'))

        # Extract strings
        self.extractStrings()

        # Run checks
        self.checkQuotes()
        self.checkSpelling()

    def extractStrings(self):
        '''Extract strings from tmx'''

        tree = etree.parse(self.tmx_file)
        root = tree.getroot()

        for tuv in root.xpath("//tuv"):
            string_id = tuv.getparent().get("tuid")
            product = string_id.split(':')[0]
            if product not in self.included_products:
                continue
            if tuv.get("{http://www.w3.org/XML/1998/namespace}lang") == "it":
                self.translations[string_id] = tuv[0].text

    def strip_tags(self, text):
        html_stripper = MLStripper()
        html_stripper.feed(text)

        return html_stripper.get_data()

    def checkQuotes(self):
        '''Check quotes'''

        # Load exceptions
        exceptions = []
        file_name = os.path.join(self.exceptions_path, 'quotes.txt')
        with open(file_name, 'r') as f:
            exceptions = []
            for line in f:
                exceptions.append(line.rstrip())

        straight_quotes = re.compile(r'\'|"')

        all_errors = []
        for message_id, message in self.translations.items():
            if message_id in exceptions:
                continue
            if message and straight_quotes.findall(message):
                if not straight_quotes.findall(self.strip_tags(message)):
                    # Message is clean after stripping HTML
                    continue
                all_errors.append(message_id)
                if self.verbose:
                    print('{}: wrong quotes\n{}'.format(message_id, message))

        with open(os.path.join(self.errors_path, 'quotes.json'), 'w') as f:
            json.dump(all_errors, f, indent=2, sort_keys=True)

    def excludeToken(self, token):
        '''Exclude specific tokens after spellcheck'''

        # Ignore acronyms (all uppercase) and token made up only by
        # unicode characters, or punctuation
        if token == token.upper():
            return True

        # Ignore domains in strings
        if any(k in token for k in ['example.com', 'mozilla.org', 'mozilla.com']):
            return True

        return False

    def checkSpelling(self):
        '''Check for spelling mistakes'''

        # Load exceptions and exclusions
        exceptions_filename = os.path.join(
            self.exceptions_path, 'spelling.json')
        with open(exceptions_filename, 'r') as f:
            exceptions = json.load(f)

        with open(os.path.join(self.exceptions_path, 'spelling_exclusions.json'), 'r') as f:
            exclusions = json.load(f)
            excluded_strings = exclusions['excluded_strings']

        '''
            Remove things that are not errors from the list of exceptions,
            e.g. after a dictionary update, and strings that don't exist
            anymore.
        '''
        keys_to_remove = []
        for message_id, errors in exceptions.items():
            if message_id not in self.translations:
                # String doesn't exist anymore
                keys_to_remove.append(message_id)
            else:
                # Check if errors are still valid
                for error in errors[:]:
                    if self.excludeToken(error) or self.spellchecker.spell(error):
                        errors.remove(error)
                    if errors == []:
                        keys_to_remove.append(message_id)

        # Remove elements after clean-up
        for id in keys_to_remove:
            del(exceptions[id])
        # Write back the updated file
        with open(exceptions_filename, 'w') as f:
            json.dump(exceptions, f, indent=2, sort_keys=True)

        punctuation = list(string.punctuation)
        stop_words = nltk.corpus.stopwords.words('italian')

        placeables = {
            '.ftl':
                [
                    # Message references, variables, terms
                    re.compile(
                        r'(?<!\{)\{\s*([\$|-]?[A-Za-z0-9._-]+)(?:[\[(]?[A-Za-z0-9_\-, :"]+[\])])*\s*\}'),
                    # DATETIME()
                    re.compile(r'\{\s*DATETIME\(.*\)\s*\}'),
                    # Variants
                    re.compile(r'\{\s*\$[a-zA-Z]+\s*->'),
                ],
            '.properties':
                [
                    # printf
                    re.compile(r'(%(?:[0-9]+\$){0,1}(?:[0-9].){0,1}([sS]))'),
                    # webl10n in pdf.js
                    re.compile(
                        r'\{\[\s?plural\([a-zA-Z]+\)\s?\]\}|\{{1,2}\s?[a-zA-Z_-]+\s?\}{1,2}'),
                ],
            '.dtd':
                [
                    re.compile(r'&([A-Za-z0-9\.]+);'),
                ],
            '.ini':
                [
                    re.compile(r'%[A-Z_-]+%'),
                ],
        }

        all_errors = {}
        total_errors = 0
        misspelled_words = {}
        for message_id, message in self.translations.items():
            # Message ID format in TMX: product:file:string_id
            filename, extension = os.path.splitext(message_id.split(':')[1])

            # Ignore excluded strings
            if message_id in excluded_strings:
                continue

            # Strip HTML
            cleaned_message = self.strip_tags(message)

            # Remove ellipsis and newlines
            cleaned_message = cleaned_message.replace('…', '')
            cleaned_message = cleaned_message.replace(r'\n', ' ')

            # Replace other characters to reduce errors
            cleaned_message = cleaned_message.replace('/', ' ')
            cleaned_message = cleaned_message.replace('=', ' = ')

            # Remove placeables from FTL and properties strings
            if extension in placeables:
                try:
                    for pattern in placeables[extension]:
                        cleaned_message = pattern.sub(
                            ' ', cleaned_message)
                except Exception as e:
                    print('Error removing placeables')
                    print(message_id)
                    print(e)

            # Tokenize sentence
            tokens = nltk.word_tokenize(cleaned_message)
            errors = []
            for i, token in enumerate(tokens):
                if message_id in exceptions and token in exceptions[message_id]:
                    continue

                """
                    Clean up tokens. Not doing it before the for cycle, because
                    I need to be able to access the full sentence with indexes
                    later on.
                """
                if token in punctuation:
                    continue

                if token.lower() in stop_words:
                    continue

                if not self.spellchecker.spell(token):
                    # It's misspelled, but I still need to remove a few outliers
                    if self.excludeToken(token):
                        continue

                    """
                    Check if the next token is an apostrophe. If it is,
                    check spelling together  with the two next tokens.
                    """
                    if i + 3 <= len(tokens) and tokens[i+1] == '’':
                        group = "".join(tokens[i:i+3])
                        if self.spellchecker.spell(group):
                            continue

                    errors.append(token)
                    if token not in misspelled_words:
                        misspelled_words[token] = 1
                    else:
                        misspelled_words[token] += 1

            if errors:
                total_errors += len(errors)
                if self.verbose:
                    print('{}: spelling error'.format(message_id))
                    for e in errors:
                        print('Original: {}'.format(message))
                        print('Cleaned: {}'.format(cleaned_message))
                        print('  {}'.format(e))
                        print(nltk.word_tokenize(message))
                        print(nltk.word_tokenize(cleaned_message))
                all_errors[message_id] = errors

        with open(os.path.join(self.errors_path, 'spelling.json'), 'w') as f:
            json.dump(all_errors, f, indent=2, sort_keys=True)

        if total_errors:
            print('Total number of strings with errors: {}'.format(len(all_errors)))
            print('Total number of errors: {}'.format(total_errors))
        else:
            print('No errors found.')
        # Display mispelled words and their count, if above 4
        threshold = 4
        above_threshold = []
        for k in sorted(misspelled_words, key=misspelled_words.get, reverse=True):
            if misspelled_words[k] >= threshold:
                above_threshold.append('{}: {}'.format(k, misspelled_words[k]))
        if above_threshold:
            print('Errors and number of occurrences (only above {}):'.format(threshold))
            print('\n'.join(above_threshold))


def main():
    script_path = os.path.abspath(os.path.dirname(__file__))

    tmx_file = os.path.join(script_path, os.pardir,
                            'data', 'it.all-projects.tmx')
    if not os.path.isfile(tmx_file):
        sys.exit(f'Missing tmx file in {tmx_file}.')

    CheckStrings(script_path, tmx_file)


if __name__ == '__main__':
    main()
