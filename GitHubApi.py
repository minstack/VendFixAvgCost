import requests, zipfile, io, os, json

class GitHubApi:
    """

        Author: Sung Min Yoon
    """

    __BASE_URL = "https://api.github.com/"
    __ENDPOINTS = {
        "latestrelease" : "repos/{0}/{1}/releases/latest",
        "createIssue" : "repos/{0}/{1}/issues",
        "createIssueComment" : "repos/{0}/{1}/issues/{2}/comments"
    }

    __owner = ''
    __headers = {"Authorization" : "", "User-Agent" : "Python 3.7/minstack-GitHubApi"}
    __repo = ''
    __repoUrl = ''

    def __init__(self, owner, token, repo):
        """

        """

        self.__owner = owner
        self.__headers["Authorization"] = "Bearer " + token
        self.__repo = repo


    def getLatestRelease(self):
        url = self.__BASE_URL + self.__ENDPOINTS['latestrelease'].format(self.__owner, self.__repo)
        print(url)
        return requests.request("GET", url, headers=self.__headers)

    def getLatestReleaseJson(self):
        return self.getLatestRelease().json()

    def getLatestReleaseUrl(self):
        release = self.getLatestReleaseJson()

        return release['html_url']

    def getLatestReleaseDownloadUrl(self):
        release = self.getLatestReleaseJson()

        return release['assets'][0]['browser_download_url']

    def downloadLatestRelease(self, path, extract=False):
        url = self.getLatestReleaseDownloadUrl()
        r = requests.get(url)

        filename = url.split('/')[-1]

        fullpath = f"{path}/{filename}"

        if r.ok:

            #this is definitely catered to .app file extracted
            #shouldn't be like this in a general class but leaving
            #it as I don't have time to figure out a general way of dealing with
            #all types and scenarios
            if extract and url.endswith(".zip"):
                '''z = zipfile.ZipFile(io.BytesIO(r.content))

                #print(z.namelist())
                with zipfile.ZipFile(f"{path}/{filename}", "r") as z:
                    names = z.namelist()

                    for n in names:
                        localPath = z.extract(n, path)
                        if n.endswith(".app"):
                            os.chmod(localPath, 755)
                        if os.path.isdir(localFilePath):
                            continue
                z.extractall(path=path)
                #print(filename)
                appfile = filename.replace(".zip", ".app")
                print(f"{path}/{appfile}")
                os.chmod(f"{path}/{appfile}", 0o755)

                #print(target)'''
                '''
                with open(f"{path}/{filename}", 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk: # filter out keep-alive new chunks
                            f.write(chunk)
                            '''

                with open(fullpath, 'wb') as f:
                    f.write(r.content)

                os.system(f"echo 'A' | unzip {fullpath} -d {path}")
                os.system(f"rm {fullpath}")

            else:

                with open(f"{path}/{filename}", 'wb') as f:
                    f.write(r.content)

        return filename

    def createIssue(self, title, body, assignees, labels):
        url = self.__BASE_URL + self.__ENDPOINTS['createIssue'].format(self.__owner, self.__repo)
        data = {
            "title" : title,
            "body" : body,
            "assignees" : assignees,
            "labels" : labels
        }

        response = requests.post(url, headers=self.__headers, data=json.dumps(data))

        return response

    def createIssueComment(self, number, comment):
        url = self.__BASE_URL + self.__ENDPOINTS['createIssueComment'].format(self.__owner, self.__repo, number)
        data = {
            "body" : comment
        }

        response = requests.post(url, headers=self.__headers, data=json.dumps(data))

        return response
