#!/usr/bin/env python
import urlparse
import json
import oauth2 as oauth

REQUEST_TOKEN_URL = 'http://api.fitbit.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://api.fitbit.com/oauth/access_token'
AUTHORIZE_URL = 'http://api.fitbit.com/oauth/authorize'

def request_tokens(consumer_key, consumer_secret):
    
    consumer = oauth.Consumer(consumer_key, consumer_secret)
    client = oauth.Client(consumer)

    # Step 1: Get a request token. This is a temporary token that is used for 
    # having the user authorize an access token and to sign the request to obtain 
    # said access token.

    resp, content = client.request(REQUEST_TOKEN_URL, "POST")
    if resp['status'] != '200':
        raise Exception("Invalid response %s." % resp['status'])

    request_token = dict(urlparse.parse_qsl(content))

    print "Request Token:"
    print "    - oauth_token        = %s" % request_token['oauth_token']
    print "    - oauth_token_secret = %s" % request_token['oauth_token_secret']
    print 

    # Step 2: Redirect to the provider. Since this is a CLI script we do not 
    # redirect. In a web application you would redirect the user to the URL
    # below.

    print "Go to the following link in your browser:"
    print "%s?oauth_token=%s" % (AUTHORIZE_URL, request_token['oauth_token'])
    print 

    # After the user has granted access to you, the consumer, the provider will
    # redirect you to whatever URL you have told them to redirect to. You can 
    # usually define this in the oauth_callback argument as well.
    accepted = 'n'
    while accepted.lower() == 'n':
        accepted = raw_input('Have you authorized me? (y/n) ')
    oauth_verifier = raw_input('What is the PIN? ')

    # Step 3: Once the consumer has redirected the user back to the oauth_callback
    # URL you can request the access token the user has approved. You use the 
    # request token to sign this request. After this is done you throw away the
    # request token and use the access token returned. You should store this 
    # access token somewhere safe, like a database, for future use.
    token = oauth.Token(request_token['oauth_token'],
        request_token['oauth_token_secret'])
    token.set_verifier(oauth_verifier)
    client = oauth.Client(consumer, token)

    resp, content = client.request(ACCESS_TOKEN_URL, "POST")
    access_token = dict(urlparse.parse_qsl(content))

    print "Access Token:"
    print "    - oauth_token        = %s" % access_token['oauth_token']
    print "    - oauth_token_secret = %s" % access_token['oauth_token_secret']
    print
    print "You may now access protected resources using the access tokens above." 
    print

def main():
    """ Request Oauth token and token secret
    """
    config = './fitbit.json'
    with open(config, 'r') as f:
        config = json.load(f)
        consumer_key = str(config['consumer_key'])
        consumer_secret = str(config['consumer_secret'])
    request_tokens(**config)
    
if __name__ == '__main__':
    main()
