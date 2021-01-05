# import json
import pandas as pd
# import pandas_gbq as pd_gbq
import urllib.request
from datetime import datetime
from bs4 import BeautifulSoup
import os

# gcp_creds_path = '/Users/jason/Documents/Jason/JobMatch/job-match-271401-74d3c9eb9112.json'
# if os.path.exists(gcp_creds_path):
#     os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'/Users/jason/Documents/Jason/JobMatch/job-match-271401-74d3c9eb9112.json'

print('here we go')

# x = '''
# { "titles":"'data+scientist', 'product+manager', 'data+analyst', 'full+stack+developer'",
# "locations":"'New+York', 'Chicago', 'San+Francisco', 'Austin', 'Seattle'"}
# '''
# test_request = json.loads(x)


def string_to_array(input_string):
    input_string = input_string.replace("'", "")
    input_string = input_string.replace(" ", "")
    array = input_string.split(',')
    return array


def search_request(request):
    try:
        request_json = request.get_json(force=True)
        print(request_json)
    except:
        print('not like this')
        return f'Error 1!'
    titles = []
    locations = []
    if request_json and 'titles' in request_json and 'locations' in request_json:
        titles = request_json['titles']
        locations = request_json['locations']
        print('We have job titles and locations')
    titles_array = string_to_array(titles)
    locations_array = string_to_array(locations)
    return titles_array, locations_array


def url_to_df(job_url, search_title, search_location):
    soup = BeautifulSoup(urllib.request.urlopen(job_url).read(), 'html.parser')
    results = soup.find_all('div', attrs={'data-tn-component': 'organicJob'})

    output_df = pd.DataFrame()

    for x in results:
        input_datetime = datetime.today().strftime("%Y%m%d %H:%M")
        input_search_title = search_title
        input_search_location = search_location
        input_company = None
        input_job_title = None
        input_location = None
        input_job_id = None
        # input_salary = None
        # input_job_url = None

        company = x.find('span', attrs={"class": "company"})
        if company:
            input_company = company.text.strip()

        job_title = x.find('a', attrs={'data-tn-element': "jobTitle"})
        if job_title:
            input_job_title = job_title.text.strip()

        job_location = x.find(
            'span', {'class': "location"}).text.replace('\n', '')
        if job_location:
            input_location = job_location

        # salary = x.find('nobr')
        # if salary:
        #     input_salary = salary.text.strip()

        job_id = x.find('a').get('id')
        if job_id:
            input_job_id = job_id[3:]
            # input_job_url = 'https://www.indeed.com/viewjob?jk='+job_id[3:]

        job_df = pd.DataFrame(data=[{
            'search_datetime': input_datetime,
            'search_title': input_search_title,
            'search_location': input_search_location,
            'title': input_job_title,
            'location': input_location,
            'company': input_company,
            'job_id': input_job_id,
        }])
        output_df = output_df.append(job_df, ignore_index=True)

    if 'search_datetime' in output_df.columns:  # return empty dataframe if no results from search
        return pd.DataFrame()

    output_df.search_datetime = pd.to_datetime(
        output_df.search_datetime, format="%Y%m%d %H:%M")
    return output_df


def search_jobs(incoming_request):
    job_titles, job_locations = search_request(incoming_request)
    job_url_template = 'https://www.indeed.com/jobs?q={title}+%2420%2C000&l={location}&start=10&sort=date'
    jobs_df = pd.DataFrame()
    i = 0
    for job_title in job_titles:
        for job_location in job_locations:
            job_url = job_url_template.format(
                title=job_title, location=job_location)
            df = url_to_df(job_url, job_title, job_location)
            jobs_df = jobs_df.append(df, ignore_index=True)
            i += 1
            if i % 50 == 0:
                results_scaled = i*50
                print('Processed {num_results} number of results.'.format(
                    num_results=results_scaled))
    date_marker = str(datetime.today().strftime("%Y%m%d"))
    pd.io.gbq.to_gbq(jobs_df, 'job_search.job_search_' +
                     date_marker,  'job-match-271401', if_exists='append')
    # pd_gbq.to_gbq(jobs_df, 'job_search.job_search_' +
    #               date_marker, if_exists='replace')
    return print('Jobs Searched')


# search_jobs(test_request)
