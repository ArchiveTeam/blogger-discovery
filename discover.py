import gzip
import re
import requests
import string
import sys
import time
import random

DEFAULT_HEADERS = {'User-Agent': 'ArchiveTeam'}


class FetchError(Exception):
    '''Custom error class when fetching does not meet our expectation.'''


def main():
    # Take the program arguments given to this script
    # Normal programs use 'argparse' but this keeps things simple
    start_num = int(sys.argv[1])
    end_num = int(sys.argv[2])
    output_filename = sys.argv[3]  # this should be something like myfile.txt.gz

    assert start_num <= end_num

    print('Starting', start_num, end_num)

    gzip_file = gzip.GzipFile(output_filename, 'wb')

    for shortcode in check_range(start_num, end_num):
        # Write the valid result one per line to the file
        line = '{0}\n'.format(shortcode)
        gzip_file.write(line.encode('ascii'))

    gzip_file.close()

    print('Done')


def check_range(start_num, end_num):
    for num in range(start_num, end_num + 1):
        shortcode = num
        url = 'https://www.blogger.com/profile/{0}'.format(shortcode)
        counter = 0

        while True:
            # Try 20 times before giving up
            if counter > 4:
                # This will stop the script with an error
                raise Exception('Giving up!')

            try:
                text = fetch(url)
            except FetchError:
                # The server may be overloaded so wait a bit
                print('Sleeping...')
                sys.stdout.flush()
                time.sleep(10)
            else:
                if text:
                    yield 'id:{0}'.format(shortcode)

                    userid = extract_handle(text)

                    if userid:
                        yield 'user:{0}'.format(userid)

                    for blog in extract_blogs(text):
                        yield 'blog:{0}'.format(blog)
                break  # stop the while loop

            counter += 1


def fetch(url):
    '''Fetch the URL and check if it returns OK.

    Returns True, returns the response text. Otherwise, returns None
    '''
    time.sleep(random.randint(10, 25))
    print('Fetch', url)
    sys.stdout.flush()

    response = requests.get(url, headers=DEFAULT_HEADERS)

    # response doesn't have a reason attribute all the time??
    print('Got', response.status_code, getattr(response, 'reason'))

    sys.stdout.flush()

    if response.status_code == 200:
        # The item exists
        if not response.text:
            # If HTML is empty maybe server broke
            raise FetchError()

        return response.text
    elif response.status_code == 404:
        # Does not exist
        return
    elif response.status_code == 503:
        # Captcha!
        Print('You are receiving a temporary captcha from Google. Sleep 45 minutes.')
        sys.stdout.flush()
        time.sleep(2700)
        return FetchError()
    else:
        # Problem
        raise FetchError()


def extract_handle(text):
    '''Return the page creator from the text.'''
    # Search for something like
    # "http://www.blogger.com/feeds/14366755180455532991/blogs"
    match = re.search(r'"https?://www\.blogger\.[a-z]+/feeds/([0-9]+)/', text)

    if match:
        return match.group(1)


def extract_blogs(text):
    '''Return a list of tags from the text.'''
    # Search for "http://onwonder.blogspot.com/"
    return re.findall(r'"(https?://[^"]+)" rel="contributor\-to nofollow"', text)

if __name__ == '__main__':
    main()
