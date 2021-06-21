import praw
import wget
import urllib.request
import json
import os
import re
import datetime as dt
from time import sleep
import sys
import search_setup

class RedditMediaScanner:
    reddit = praw.Reddit("bot1")

    sub = ""
    submissions = ""
    search_subreddit = ""
    search_terms = [""]
    output_directory = "./DefaultDirectory/"
    url_db_path = ""
    file_extensions = [""]
    url_types = [""]
    search_limit = 1024
    allow_nsfw = False
    allow_stream = False
    split_folders = True
    processed_urls = []

    def __init__(self):
        print("Reddit Media Scan Bot Initialized!")
        self.setup_configs()

        print(dt.datetime.now())
        print("Current user: %s" % self.reddit.user.me())
        print("Subreddit - %s" % self.search_subreddit)
        print("Keywords - %s" % self.search_terms)
        print("File Extensions - %s" % self.file_extensions)
        print("URL Types - %s"  % self.url_types)
        print("URL Database path - %s" % self.url_db_path)

        self.sub = self.reddit.subreddit(self.search_subreddit)
        self.submissions = list(self.sub.new(limit=self.search_limit))
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def setup_configs(self):
        setup = search_setup.ConfigReader()
        setup.read_config()
        self.search_subreddit = setup.search_subreddit
        self.search_terms = setup.search_terms
        self.output_directory = setup.output_directory
        self.url_db_path = setup.url_db_path
        self.file_extensions = setup.file_extensions
        self.url_types = setup.url_types
        self.search_limit = setup.search_limit
        self.allow_nsfw = setup.allow_nsfw
        self.allow_stream = setup.allow_stream
        self.split_folders = setup.split_folders

        self.processed_urls = self.get_processed_urls()

        self.search_terms = [str.upper(x).strip(' ') for x in self.search_terms]

        if (self.split_folders):
            for ext in self.file_extensions:
                new_dir = ("%s%s" % (self.output_directory, ext))
                if not os.path.exists(new_dir):
                    os.makedirs(new_dir)

    def format_gfy(self, submissionUrl):
        subSplit = submissionUrl.rsplit('/', 1)[1].rsplit('-', 1)[0].rsplit('.gif', 1)[0]
        jsonURL = "http://gfycat.com/cajax/get/%s" % subSplit
        with urllib.request.urlopen(jsonURL) as url:
            gfyData = json.loads(url.read().decode('utf-8'))
            gifURL = gfyData.get('gfyItem').get('gifUrl')
            submissionUrl = gifURL
        submissionUrl = gifURL
        return submissionUrl

    def file_already_exists(self, fileName):
        mapsPath = self.output_directory + "../"
        print(fileName)
        print(mapsPath)
        for dir, sub_dirs, files in os.walk(mapsPath):
            if fileName in files:
                return True
        return False 

    def fix_file_name(self, fileName):
        fileName = re.sub('[^A-Za-z0-9]+', '', fileName)
        return fileName

    def get_processed_urls(self):
        urls = []
        if os.path.exists(self.url_db_path):
            f = open(self.url_db_path, 'r+')
            for line in enumerate(f):
                urls.append(line[1].strip().split(',')[0])
            f.close()
        return urls

    def add_to_urls_db(self, urls):
        with open(self.url_db_path, 'a') as f:
            for url in urls:
                f.write(url + '\n')

    def historical_scan(self):
        print("\nHistorical Submissions Capture Active...")
        print("_______________________")
        new_urls = []
        for submission in self.submissions:
#            if any(re.search(term, str.upper(submission.title)) for term in self.search_terms):
            if any(x in str.upper(submission.title) for x in self.search_terms):
                if submission.over_18:
                    if self.allow_nsfw is False:
                        continue
                submission_url = submission.url
                if submission_url in self.processed_urls or submission_url in new_urls:
                    print("URL %s was already treated" % submission_url)
                    print("Skipping...")
                    print("_______________________")
                    continue
                if any(y in submission_url for y in self.url_types):
                    if "gfycat" in submission_url:
                        if "albums" in submission_url:
                            continue
                        submission_url = self.format_gfy(submission_url)

                    if any(z in submission_url for z in self.file_extensions):
                        file_name = self.fix_file_name(submission.title)
                        file_dir = ("%s%s.%s" % (self.output_directory, file_name, submission_url.rsplit('.', 1)[1]))
                        if (self.split_folders):
                            dir_check = "." + submission_url.rsplit('.', 1)[1]
                        else:
                            dir_check = ""
                        if dir_check in self.file_extensions:
                            file_dir = ("%s%s/%s.%s" % (
                            self.output_directory, dir_check, file_name, submission_url.rsplit('.', 1)[1]))

                        if self.file_already_exists(file_name + "." + submission_url.rsplit('.', 1)[1]): # os.path.isfile(file_dir):
                            print("File Already Exists - %s" % file_dir)
                            if not submission_url in self.processed_urls:
                                new_urls.append(submission_url + "," + file_name)
                            print("Skipping...")
                            print("_______________________")
                            continue
                        else:
                            wget.download(submission_url, out=file_dir)
                            print("\nFile Size: %s KB" % (os.path.getsize(file_dir) / 1024))
                            new_urls.append(submission_url + "," + file_name)
                            print("Waiting for new file...")
                            print("-----------------------")
        print("Historical Media Saved!")
        self.add_to_urls_db(new_urls)
        # print("Downloaded %s files" % len(new_urls))
        print("_______________________")

    def realtime_scan(self):
        print("\nReal Time Media Capture Active...")
        print("_______________________")
        for submission in self.sub.stream.submissions():
            if any(x in str.upper(submission.title) for x in self.search_terms):
                if submission.over_18:
                    if self.allow_nsfw is False:
                        continue
                submission_url = submission.url
                if any(y in submission_url for y in self.url_types):
                    if "gfycat" in submission_url:
                        submission_url = self.format_gfy(submission_url)

                    if any(z in submission_url for z in self.file_extensions):
                        print(submission_url)
                        file_name = self.fix_file_name(submission.title)
                        file_dir = ("%s%s.%s" % (self.output_directory, file_name, submission_url.rsplit('.', 1)[1]))
                        if (self.split_folders):
                            dir_check = "." + submission_url.rsplit('.', 1)[1]
                        else:
                            dir_check = ""
                        if dir_check in self.file_extensions:
                            file_dir = ("%s%s/%s.%s" % (
                            self.output_directory, dir_check, file_name, submission_url.rsplit('.', 1)[1]))
                        

                        if not os.path.exists('/tmp/test'):
                            os.mknod('/tmp/test')

                        if os.path.isfile(file_dir):
                            print("Already Exists - %s" % file_dir)
                            print("Skipping...")
                            print("_______________________")
                            continue
                        else:
                            print("Downloaded to - %s" % file_dir)
                            wget.download(submission_url, out=file_dir)
                            print("\nFile Size: %s KB" % (os.path.getsize(file_dir) / 1024))
                        print("Waiting for new file...")
                        print("-----------------------")
                        sleep(2)

def main():
    program = RedditMediaScanner()
    startTime = dt.datetime.now()
    program.historical_scan()
    endTime = dt.datetime.now()
    print("Runtime: {}".format(endTime - startTime))
    print("\n\n")

    if program.allow_stream:
        startTime = dt.datetime.now()
        program.realtime_scan()
        endTime = dt.datetime.now()
        print("Runtime: {}".format(endTime - startTime))

    sys.exit(0)

if __name__ == "__main__":
    main()