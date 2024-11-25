import requests
import urllib3
import http.client
import traceback
import pprint
import os
import json
from requests_kerberos import HTTPKerberosAuth
import pandas as pd
requests.packages.urllib3.disable_warnings()


class HsdConnector:
    def _get_response(self, req, headers):
        """
        def _get_response(self, req, headers):
        This function sends a GET request to a specified URL and returns the response data.

        Parameters:
        req (str): The URL to send the GET request to.
        headers (dict): The headers to include in the GET request.

        Returns:
        dict: The response data parsed as JSON.

        Raises:
        HTTPError: If the GET request is not successful (i.e., if the response status code is not 200).
        Exception: If there is an error when trying to parse the response data as JSON.
    """
        # Send a GET request to the specified URL (req) with the provided headers
        response = requests.get(req, auth=HTTPKerberosAuth(), verify=False, headers=headers)
        # If the response is successful (status code 200)
        if response.ok:
            try:
                # Try to parse the response data as JSON
                response_data = response.json()
                # Return the parsed data
                return response_data
            except Exception as e:
                # If an error occurs during parsing, raise the exception
                raise e
        else:
            # If the response is not successful, raise an HTTPError for the given status code
            response.raise_for_status()

    def _set_response(self, req, headers, data, operation="put"):
        """
        This function sends a PUT or POST request to a specified URL with provided data and returns the response.
        Parameters:
        req (str): The URL to send the PUT or POST request to, as needed by HSDES REST API
                   More info: More info on this method: https://wiki.ith.intel.com/display/HSDESWIKI/Intro+to+REST+API
        headers (dict): The headers to include in the PUT or POST request.
        data (dict): The data to include in the PUT or POST request.
        operation (str): one of 'put' or 'post'

        Returns:
        dict: The response data parsed as JSON if possible, otherwise the raw response.

        Raises:
        HTTPError: If the PUT request is not successful (i.e., if the response status code is not 200).
        """

        # Send a PUT/POST request to the specified URL (req) with the provided headers and data
        if operation == "put":
            response = requests.put(req, auth=HTTPKerberosAuth(), verify=False, headers=headers, data=data)
        elif operation == "post":
            response = requests.post(req, auth=HTTPKerberosAuth(), verify=False, headers=headers, data=data)
        else:
            raise ValueError("Unsupported request operation: %s"%(repr(operation),))

        # If the response is successful (status code 200)
        if response.ok:
            try:
                # Try to parse the response data as JSON
                response = response.json()
            except Exception as e:
                # If an error occurs during parsing, return the raw response
                return response
            # If parsing is successful, return the parsed data
            return response
        else:
            # If the response is not successful, raise an HTTPError for the given status code
            response.raise_for_status()

    def get_query(self, q_id, max_number_of_entries_to_read):
        """
            https://hsdes-api.intel.com/rest/query/{query_id}
            :param q_id: query id
            :return: json of all the hsd returned from the query
            """
        req = "https://hsdes-api.intel.com/rest/query/" + str(
            q_id) + "?expand=metadata&start_at=1&max_results=" + max_number_of_entries_to_read
        headers = {'Content-type': 'application/json'}
        return self._get_response(req, headers)

    def get_hsd(self, hsd_id, fields=None):
        """
        Fetches detailed information about an HSD page using its ID. The method sends a GET request to the HSD API and
        retrieves the data associated with the given ID. The data is returned as a dictionary.

        Note: The HSD API requires Kerberos authentication. Meaning it can only be executed locally and not over cloud.

        Parameters:
        id (str): The ID of the HSD page to fetch information for.
        fields (List<str>): fields to include in the response, list of strings (optional). If not defined, returns all fields.

        Returns:
        dict: A dictionary containing detailed information about the HSD page. The dictionary includes the data
        associated with the given ID. If the ID does not exist or the request fails, the method raises an exception.

        Raises:
        requests.exceptions.HTTPError: If the HTTP request encounters an error or if the response status code is not 200 OK.
        urllib3.exceptions.MaxRetryError: If the HSD could not be found and reached MAX retries count (10)
        requests.exceptions.ProxyError: Problem with proxy settings
        http.client.RemoteDisconnected: During the query the remote was disconnected

        https://hsdes-api.intel.com/rest/article/{id}?fields={field1}%2C%20{field1}%2C%20{field1}...
        :param hsd_id: the hsd id
        :param fields: list of field names
        :return:json of all the fields returned from the hsd
        """
        
        if fields == "":  # Backwards compatibility
            fields = None
        
        assert fields is None or (len(fields) > 0 and type(fields) != str and all([type(f) == str for f in fields])), \
            "fields must be None or a list\iterator of strings. Got %s."%(repr(fields),)
        retry = 10
        while (retry > 0):
            try:
                req = "https://hsdes-api.intel.com/rest/article/" + str(hsd_id)
                if fields is not None:
                    req += "?fields=" + "%2C%20".join(fields)
                headers = {'Content-type': 'application/json'}
                # print req
                response_data = self._get_response(req, headers)
                if "data" in response_data:
                    return response_data["data"][0]
                else:
                    raise Exception('Could not find "data" in response...')
            except urllib3.exceptions.MaxRetryError:
                print('Got "urllib3.exceptions.MaxRetryError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except requests.exceptions.ProxyError:
                print('Got "requests.exceptions.ProxyError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except http.client.RemoteDisconnected:
                print('Got "http.client.RemoteDisconnected" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except Exception as e:
                print(
                    'Got unknown exception: {}, retrying {} more attempts'.format(traceback.format_exc(), (retry - 1)))
                retry -= 1

    def get_hsd_revision_changeset(self, hsd_id, rev):
        """
        https://hsdes-api.intel.com/rest/article/{id}/{rev}/changeset
        :param hsd_id: the hsd id
        :param rev: rev of the article.
        :return:json of all the fields returned from the hsd revision changeset
        """
        req = "https://hsdes-api.intel.com/rest/article/{}/{}/changeset".format(hsd_id, rev)
        headers = {'Content-type': 'application/json'}
        # print req
        response_data = self._get_response(req, headers)
        if "changeset" in response_data:
            return response_data["changeset"][0]
        else:
            raise Exception('Could not find "changeset" in response...')

    def get_hsd_user_info(self, user_name):
        """
        https://hsdes-api.intel.com/rest/user/{username}?expand=personal
        :param user_name: the hsd user name
        :return:json of all the fields returned from the hsd
        """
        req = "https://hsdes-api.intel.com/rest/user/{username}?expand=personal".format(username=user_name)
        headers = {'Content-type': 'application/json'}
        # print req
        response_data = self._get_response(req, headers)
        if "data" in response_data:
            return response_data["data"][0]
        else:
            raise Exception('Could not find "data" in response...')

    def set_hsd(self, hsd_id, tenant, subject, fields="", values="", operation="put"):
        """
        https://hsdes-api.intel.com/rest/article/{id}?fields={field1}%2C%20{field1}%2C%20{field1}...
        More info on this method: https://wiki.ith.intel.com/display/HSDESWIKI/Intro+to+REST+API
        
        :param tenant: tenant from which to take the item
        :param subject: subject of the item
        :param hsd_id: the hsd id
        :param fields: list of field names
        :param values: values of the fields
        :param operation: one of 'put' or 'post' as needed by HSDES Rest-API.
        :return:json of all the fields returned from the hsd
        """
        
        req = "https://hsdes-api.intel.com/rest/article" + (("/"+str(hsd_id)) if hsd_id is not None else "")
        headers = {'Content-type': 'application/json'}
        data = '{"tenant": "' + str(tenant) + '","subject": "' + str(subject) + '",'
        if len(fields) > 0:
            data += '"fieldValues": ['
            data += '{"' + str(fields[0]) + '": ' + json.dumps(values[0].replace("\n","\r\n")) + '}'
            for i in range(len(fields) - 1):
                data += ',{"' + str(fields[i + 1]) + '": ' + json.dumps(values[i + 1].replace("\n","\r\n")) + '}'
            data += ']}'
        
        return self._set_response(req, headers, data, operation = operation)
        
    def set_comment(self, tenant, parent_id, description, send_mail = False):
        '''
        Insert a new comment into an existing HSD
        More info: https://wiki.ith.intel.com/display/HSDESWIKI/Intro+to+REST+API#IntrotoRESTAPI-Insertacomment
        
        :param tenant: tenand name for the parent HSD
        :param parent_id: parent HSD id
        :param description: Comment description. Supports HTML syntax (i.e., line breaks should be insterted as '<br/>'.
        :param send_mail: have HSD system send a notification email for the comment insert
        '''
        res = self.set_hsd(None, tenant=tenant, subject="comments", operation="post",
                    fields=["description",
                            "parent_id",
                            "send_mail"], 
                    values=[description,
                            parent_id,
                            "true" if send_mail else "false",
                            ])
        return res['new_id']

    def get_hsd_links(self, hsd_id, fields=""):
        """
                    Fetches detailed information about all of an HSD page's linked articles using its ID. The method sends a
                    GET request to the HSD API and retrieves the data associated with the given ID. The data is returned as
                    a dictionary.

                    Note: The HSD API requires Kerberos authentication. Meaning it can only be executed locally and not over cloud.

                    Parameters:
                    id (str): The ID of the HSD page to fetch information for.
                    fields (List<str>): fields to include in the response, list of strings (optional)

                    Returns:
                    dict: A dictionary containing detailed information about the HSD page. The dictionary includes the data
                    associated with the given ID. If the ID does not exist or the request fails, the method raises an exception.

                    Raises:
                    requests.exceptions.HTTPError: If the HTTP request encounters an error or if the response status code is not 200 OK.
                    urllib3.exceptions.MaxRetryError: If the HSD could not be found and reached MAX retries count (10)
                    requests.exceptions.ProxyError: Problem with proxy settings
                    http.client.RemoteDisconnected: During the query the remote was disconnected

                    https://hsdes-api.intel.com/rest/article/{id}?fields={field1}%2C%20{field1}%2C%20{field1}...
                    :param hsd_id: the hsd id
                    :param fields: list of field names
                    :return:json of all the fields for all the linked articles returned from the given hsd
            """

        retry = 10
        while (retry > 0):
            try:
                req = "https://hsdes-api.intel.com/rest/article/" + str(hsd_id) + "/links"
                if len(fields) > 0:
                    req += "?fields=" + str(fields[0])
                    for i in range(len(fields) - 1):
                        req += "%2C%20" + str(fields[i + 1])
                    req += "&showHidden=Y&showDeleted=N"
                headers = {'Content-type': 'application/json'}
                # print req
                response_data = self._get_response(req, headers)
                if "responses" in response_data:
                    return response_data
                else:
                    raise Exception('Could not find "data" in response...')
            except urllib3.exceptions.MaxRetryError:
                print('Got "urllib3.exceptions.MaxRetryError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except requests.exceptions.ProxyError:
                print('Got "requests.exceptions.ProxyError" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except http.client.RemoteDisconnected:
                print('Got "http.client.RemoteDisconnected" exception, retrying {} more attempts'.format(retry - 1))
                retry -= 1
            except Exception as e:
                print(
                    'Got unknown exception: {}, retrying {} more attempts'.format(traceback.format_exc(), (retry - 1)))
                retry -= 1


if __name__ == "__main__":

    df = pd.read_csv("./Updated_failures.csv")
    hsdes_links = df['hsdes_link']
    username = os.environ.get("USERNAME", "ginaburt")
    user = input("Give me an IDSD (user) go get info from HSD system [%s]: "%(username,))
    if user == "":
        user = username
    for link in hsdes_links.dropna():
        print(link)
        val = link.split('/')
        hsd_id = val[6]
               
        hsd = HsdConnector()
        
        # Get HSD data
        data = hsd.get_hsd(hsd_id)
        print("HSD info:\n    %s"%(pprint.pformat(data).replace("\n", "\n    "),))

        # Get user information from HSD
        user = hsd.get_hsd_user_info(user)
        print("\n\nUser info:\n    %s"%(pprint.pformat(user).replace("\n", "\n    "),))
        break
    