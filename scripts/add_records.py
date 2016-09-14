"""
Simple script to add docs to poseidon
mongo database.

@author: lanhamt
Created on September 13, 2016
"""
import requests

doc_ids = []


def get_host():
    while True:
        host = input("hostname for storage interface: ")
        if host:
            return host


def add_docs(host, db, coll, doc, port='28000'):
    try:
        add_doc_uri = 'http://' + host + ':' + port + \
                      '/v1/storage/add_one_doc/{database}/{collection}'.format(
                       database=db,
                       collection=coll)
        resp = requests.post(add_doc_uri, json=doc)
        print 'doc id is: ', resp.text
        doc_ids.append(resp.text)
    except Exception, e:
        print str(e)


def get_doc(doc_id, host, port, db, coll):
    try:
        uri = 'http://' + host + ':' + port + \
              '/v1/storage/doc/{database}/{collection}/{doc_id}'.format(
               database=db,
               collection=coll,
               doc_id=doc_id)
        resp = requests.get(uri)
        print resp.text
    except Exception, e:
        print str(e)


if __name__ == '__main__':
    host = get_host()
    #print doc_ids
