import streamlit as st
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


def scrape_and_save(startPage, endPage):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chromedriver_path = "./chromedriver"
        driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)

        base_url = "https://tenders.etimad.sa/Tender/AllTendersForVisitor?&MultipleSearch=&TenderCategory=&ReferenceNumber=&TenderNumber=&agency=&ConditionaBookletRange=&PublishDate=&LastOfferPresentationDate=&LastOfferPresentationDate=&TenderAreasIdString=&TenderTypeId=NaN&TenderSubActivityId=&AgencyCode=&FromLastOfferPresentationDateString=&ToLastOfferPresentationDateString=&SortDirection=DESC&Sort=SubmitionDate&PageSize=24&IsSearch=true&ConditionaBookletRange=&PublishDate=undefined&PageNumber={}"

        date_of_publication = []
        type_of_tender = []
        tender_title = []
        tendering_authority = []

        progress_bar = st.progress(0)

        for page_number in range(startPage, endPage+1):
            url = base_url.format(page_number)
            driver.get(url)

            try:
                # waiting for tender_divs to be visible
                WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.col-12.col-md-12.mb-4")))
            except TimeoutError:
                print(f"Timeout on page {page_number} (this page probably doesn't have any data)")
                continue

            html_after_js = driver.page_source
            soup = BeautifulSoup(html_after_js, 'html.parser')

            tender_divs = soup.find_all('div', class_='col-12 col-md-12 mb-4')
            date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')

            for div in tender_divs:
                text = div.get_text(strip=True)
                match = date_pattern.search(text)
                date_of_publication.append(match.group() if match else "")

                type_span = div.find('span', class_='badge badge-primary')
                type_of_tender.append(type_span.get_text(strip=True) if type_span else "")

                title_h3 = div.find('h3')
                tender_title.append(title_h3.get_text(strip=True) if title_h3 else "")

                authority_p = div.find('div', class_='col-12').find('p')
                tendering_authority.append(authority_p.get_text(strip=True) if authority_p else "")

            progress_bar.progress((page_number - startPage + 1) / (endPage - startPage + 1), f"Progress: {int((page_number - startPage + 1) / (endPage - startPage + 1) * 100)}%")
        driver.quit()



        df = pd.DataFrame({
            "Date of Publication": date_of_publication,
            "Type of Tender": type_of_tender,
            "Tender Title": tender_title,
            "Tendering Authority": tendering_authority,
        })

        csv_content = df.to_csv(index=False)

        st.write("")
        st.markdown(
            """
            <h4 style='color: #005b4e;'>Preview - top 5 rows:</h4>
            """,
            unsafe_allow_html=True
        )
        st.dataframe(df.head(5)) 
        st.download_button(
            label="Download CSV",
            data=csv_content,
            file_name=f"result({startPage}-{endPage}).csv",
            mime="text/csv",
        )

    except Exception as e:
        st.error("Exception occurred: {}".format(str(e)))



def main():
    
    st.markdown(
        """
        <h1 style='text-align: center; color: #1c8657; margin-bottom: -8px;'>Scrape & Save</h1>
        <h3 style='text-align: center; color: #005b4e;'>Etimad Tender Scraping App</h3>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")
    st.write("")
    
    col1, col2 = st.columns(2) 
    with col1: start_page = st.number_input("Start Page Number", min_value=1, step=1)
    with col2: end_page = st.number_input("End Page Number", min_value=1, step=1)

    if st.button("Scrape Data", key="scrape-button"):
        st.write("")
        st.write("")
        with st.spinner("Scraping in progress..."):
            scrape_and_save(start_page, end_page)



if __name__ == "__main__": 
    main()
