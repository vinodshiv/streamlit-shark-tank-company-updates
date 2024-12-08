import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

# Base URLs
company_list_url = "https://abc.com/news/920582c3-2083-45bc-81c9-95e33c5a76e9/category/706923"
shark_tank_search_url = "https://sharktankrecap.com/?s="
image_url = "https://cdn1.edgedatg.com/aws/v2/abc/SharkTank/showimages/5005ca5bbbe24f4b83960ac543dbe14d/2016x807-Q75_5005ca5bbbe24f4b83960ac543dbe14d.jpg"

# Function to fetch the list of companies and the last updated date
def fetch_company_list_and_last_updated():
    response = requests.get(company_list_url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        company_list = []
        last_updated = None

        # Locate the element containing the company list
        article_text_div = soup.find('div', class_='article__text')
        if article_text_div:
            paragraphs = article_text_div.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)

                # Extract the "Last updated" information
                if "Last updated" in text:
                    last_updated = text.split("Last updated:")[-1].strip()

                # Extract company names
                if "<br/>" in str(p):  # Look for the paragraph with the company list
                    companies = str(p).split("<br/>")
                    for company in companies:
                        company = BeautifulSoup(company, "html.parser").get_text(strip=True)
                        if company and "Last updated" not in company:
                            company_list.append(company)

        return company_list, last_updated
    else:
        raise Exception(f"Failed to fetch company list. Status code: {response.status_code}")

# Function to search for a company on SharkTankRecap
def search_company(company_name):
    search_url = shark_tank_search_url + company_name.replace(" ", "+")
    response = requests.get(search_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for article in soup.find_all('article'):
            title_tag = article.find('h2', class_='entry-title')
            if title_tag and title_tag.a:
                title = title_tag.a.text.strip()
                link = title_tag.a['href']
                results.append({'title': title, 'link': link})
        return results
    else:
        st.error(f"Failed to fetch search results. Status code: {response.status_code}")
        return []


# Function to scrape raw HTML of a page
def scrape_page(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code == 200:
        return response.text  # Return raw HTML content
    else:
        raise Exception(f"Failed to fetch the page: {url}, Status Code: {response.status_code}")
    

# Function to search for keywords in content and extract matching paragraphs
def extract_paragraphs(content, keywords):
    paragraphs = content.split("\n")
    matching_paragraphs = [p for p in paragraphs if any(keyword.lower() in p.lower() for keyword in keywords)]
    return matching_paragraphs

# Function to split content into sentences
def split_into_sentences(content):
    # Split content into sentences using regex for punctuation delimiters
    return re.split(r'(?<=[.!?])\s+', content)


# Function to extract paragraphs and filter based on keywords
def extract_and_filter_paragraphs_html(content, include_keywords, exclude_keywords, stop_keywords):
    soup = BeautifulSoup(content, "html.parser")
    paragraphs = soup.find_all("p")
    matching_paragraphs = []
    
    for paragraph in paragraphs:
        text = paragraph.get_text(strip=True)
        
        # Stop processing if a stop keyword is found
        if any(stop_word.lower() in text.lower() for stop_word in stop_keywords):
            break

        # Include paragraph if it matches include_keywords and doesn't match exclude_keywords
        if any(include_keyword.lower() in text.lower() for include_keyword in include_keywords) and \
           not any(exclude_keyword.lower() in text.lower() for exclude_keyword in exclude_keywords):
            matching_paragraphs.append(paragraph)
    
    return matching_paragraphs



# Streamlit App
st.set_page_config(page_title="🦈 Appeared on Shark Tank Updates", layout="centered")
st.markdown("<h2 style='text-align: center; color: #315D94;'>🦈 \"Appeared on Shark Tank\" Updates</h2>", unsafe_allow_html=True)
st.caption(f"Looks up abc.com for official companies on Shark Tank, gets current status update")

col1, col2, col3 = st.columns(3)
with col2:
    st.image(image_url, width=600)

st.markdown("---")
# Step 1: Fetch and display company list
st.markdown("#### :orange[Select/Search for a company]")
with st.spinner("Fetching company list..."):
    try:
        company_list, last_updated = fetch_company_list_and_last_updated()
    except Exception as e:
        st.error(str(e))
        company_list = []
        last_updated = None

if company_list:
    st.caption(f"Source: [abc.com]({company_list_url}) | Last updated: {last_updated}")
    selected_company = st.selectbox("Select for a search restult",
                                     company_list, index=None, label_visibility="collapsed")

    if selected_company:
        # Step 2: Search for the selected company on SharkTankRecap
        with st.spinner(f"Searching for {selected_company} ..."):
            search_results = search_company(selected_company)

        if search_results:
            # Display search results
            st.markdown("#### :green[Select a search result]")
            options = [f"{result['title']}" for result in search_results]
            selected_option = st.selectbox("Select a result to scrape:", options, label_visibility="collapsed")

            if selected_option:
                # Scrape the selected page
                selected_index = options.index(selected_option)
                selected_result = search_results[selected_index]
                with st.spinner(f"Summarizing from [{selected_result['title']}]({selected_result['link']})"):
                
                    page_content = scrape_page(selected_result['link'])

                    # Step 3: Extract matching paragraphs using HTML filtering
                    include_keywords = ["update", "at the time this writing"]
                    exclude_keywords = ["keep reading"]
                    stop_keywords = ["other companies", "other company",
                                    "other Shark Tank","Before you go", "For more updates from","links below"]

                    #st.write(page_content)
                    matching_paragraphs_html = extract_and_filter_paragraphs_html(page_content, include_keywords, exclude_keywords, stop_keywords)

                    if matching_paragraphs_html:
                        st.markdown("---")
                        st.subheader(":blue[Company Updates]")
                        st.caption(f"Source: [{selected_result['title']}]({selected_result['link']})")
                        for paragraph in matching_paragraphs_html:
                            st.markdown(f"- {paragraph.get_text(strip=True)}")
                    st.markdown("---")

                        # else:
                        #     st.warning("No matching paragraphs found.")


        else:
            st.warning("No search results found.")
else:
    st.warning("No companies found.")
