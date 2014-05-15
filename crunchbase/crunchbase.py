
import requests
import urllib
import ujson as json

class Crunchbase(object):
    BASE_URI = "http://api.crunchbase.com"
    ENTITY_TYPES = ('company', 'companies',
                    'product', 'products',
                    'person', 'people',
                    'financial-organization', 'financial-organizations',
                    'service-provider', 'service-providers')

    def __init__(self, apikey=None, version=1):
        self._apikey = apikey
        self.version = version
        self.uri = self.BASE_URI + "/v/%d" % version + "/{endpoint}.js"
        self.last_called_uri = None
    
    def uri_for(self, entity_type=None, entity_name=None):
        if entity_type not in self.ENTITY_TYPES:
            raise Exception("Invalid `entity_type`")
        if entity_name:
            endpoint = "{0}/{1}".format(entity_type, entity_name)
        else:
            endpoint = entity_type
        return self.uri.format(endpoint=endpoint)

    def _get(self, url, data=None):
        try:
            r = requests.get(url, params=data)
            self.last_called_uri = r.url
            return r.json()
        except:
            return None

    def call_api(self, entity_type, entity_name=None, page=None):
        uri = self.uri_for(entity_type, entity_name)
        payload = {'api_key': self._apikey}
        if page:
            payload['page'] = page
        return self._get(uri, payload)

    # start methods for CB
    def search(self, keyword, entity_type=None, field=None):
        uri = self.uri.format(endpoint='search')
        payload = {"query": keyword}
        if entity_type:
            payload['entity'] = entity_type
        if field:
            payload['field'] = field
        payload.update({'api_key': self._apikey})
        r = requests.get(uri, params=payload)
        return json.loads(r.text)

    def company(self, name):
        return self.call_api('company', name)

    def all_companies(self):
        return self.call_api('companies', page=1)

    def person(self, name):
        return self.call_api('person', name)
    
    def all_persons(self):
        return self.call_api('people', page=1)

    def financial_org(self, name):
        return self.call_api('financial-organization', name)
    
    def all_financial_orgs(self):
        return self.call_api('financial-organizations', page=1)

    def product(self, name):
        return self.call_api('product', name)
    
    def all_products(self):
        return self.call_api('products', page=1)

    def service_provider(self, name):
        return self.call_api('service-provider', name)
    
    def all_service_providers(self):
        return self.call_api('service-providers', page=1)


