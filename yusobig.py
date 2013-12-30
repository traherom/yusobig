#!/usr/bin/env python

import pprint
import sys
import operator

from dropbox import client, rest, session

# XXX Fill in your consumer key and secret below
# You can find these at http://www.dropbox.com/developers/apps
APP_KEY = ''
APP_SECRET = ''

TOKEN_FILE = 'yusobig.token'

api_client = None

def do_init():
    """login to dropbox if we have a oauth token"""
    global api_client
    api_client = None
    try:
        serialized_token = open(TOKEN_FILE).read()
        if serialized_token.startswith('oauth2:'):
            access_token = serialized_token[len('oauth2:'):]
            api_client = client.DropboxClient(access_token)
            print "[loaded OAuth 2 access token]"
        else:
            print "Malformed access token in %r." % (TOKEN_FILE,)
    except IOError:
        do_login()

    if api_client is None:
        print "Unable to login to Dropbox, please try again"
        quit()

def do_login():
    """log in to a Dropbox account"""
    global api_client
    flow = client.DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)
    authorize_url = flow.start()
    sys.stdout.write("1. Go to: " + authorize_url + "\n")
    sys.stdout.write("2. Click \"Allow\" (you might have to log in first).\n")
    sys.stdout.write("3. Copy the authorization code.\n")
    code = raw_input("Enter the authorization code here: ").strip()

    try:
        access_token, user_id = flow.finish(code)
    except rest.ErrorResponse, e:
        stdout.write('Error: %s\n' % str(e))
        return

    with open(TOKEN_FILE, 'w') as f:
        f.write('oauth2:' + access_token)
    api_client = client.DropboxClient(access_token)

def show_status():
    """print email address of account we're using"""
    global api_client

    print "Scanning files in account for:", api_client.account_info()['email']

def sizeof_bytes_to_human(num):
    """returns a human-readable version of a size in bytes"""
    for x in ['bytes','KB','MB','GB']:
        if num < 1024.0 and num > -1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')

def get_folder_sizes(base='/', pp=None):
    """returns the total size of the given folder and all subfolders"""
    global api_client

    if pp is None:
        pp = pprint.PrettyPrinter(indent=2)

    #print 'Entering', base

    curr_files = api_client.metadata(base)
    for key, content in enumerate(curr_files['contents']):
        if content['is_dir']:
            # Get everything in this dir and total it to get the folder size
            content = get_folder_sizes(content['path'], pp)
            curr_files['bytes'] += content['bytes']
            curr_files['contents'][key] = content

        else:
            # Add to the current directory's size
            curr_files['bytes'] += content['bytes']

    return curr_files

def flatten_files(files, skip_files=False):
    flattened = {}

    # Add all contents
    for curr in files['contents']:
        if curr['is_dir']:
            flattened = dict(flattened.items() + flatten_files(curr, skip_files).items())
        elif not skip_files:
            flattened[curr['path']] = curr['bytes']

    # And add the top level itself (really only need for the very top item)
    flattened[files['path']] = files['bytes']

    return flattened

def sort_by_size(files):
    return sorted(files.iteritems(), key=operator.itemgetter(1))

def list_files(files):
    for path, size in files:
        print '{}: {}'.format(path, sizeof_bytes_to_human(size))

def main():
    global api_client
    if APP_KEY == '' or APP_SECRET == '':
        exit("You need to set your APP_KEY and APP_SECRET!")
    
    do_init()
    show_status()

    files = get_folder_sizes()
    files = flatten_files(files, True)
    files = sort_by_size(files)
    list_files(files)

if __name__ == '__main__':
    main()

