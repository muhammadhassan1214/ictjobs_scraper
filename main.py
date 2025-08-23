import re
import pandas as pd
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from utils import *

def _to_int(text: str) -> int:
    m = re.search(r'\d+', text or '')
    return int(m.group()) if m else 0

def _click_next(driver, timeout: int = 10) -> bool:
    try:
        current = driver.current_url
        btn = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "next-link"))
        )
        btn.click()
        WebDriverWait(driver, timeout).until(EC.url_changes(current))
        return True
    except Exception:
        return False

def _read_done_set(path: str = 'done.txt') -> set[str]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return set(l.strip() for l in f if l.strip())
    except FileNotFoundError:
        return set()

def accept_cookies(driver):
    try:
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()= 'Accept All']/ancestor::button"))
        )
        btn.click()
    except Exception:
        pass

def _safe_language_list(driver):
    locator = (By.XPATH, "//span[@class= 'job-language-name job-language-name--proficient']")
    for _ in range(3):
        try:
            els = driver.find_elements(*locator)
            texts = []
            for el in els:
                texts.append(el.text.strip())
            half = len(texts) // 2
            return texts[:half]
        except StaleElementReferenceException:
            time.sleep(0.2)
    return []

def _safe_similar_offers(driver):
    locator = (By.XPATH, "//span[@class= 'job-info']/a")
    for _ in range(3):
        try:
            els = driver.find_elements(*locator)
            return [(el.get_attribute("href") or "").strip() for el in els]
        except StaleElementReferenceException:
            time.sleep(0.2)
    return []

def main():
    output_file_name = 'ictjob_data.csv'
    driver = get_normal_driver()
    loop_count = page_count = job_count = 1
    jobs_per_page = 20
    try:
        done_urls = _read_done_set('done.txt')
        driver.get("https://www.ictjob.be/en/search-it-jobs")
        accept_cookies(driver)
        total_jobs_txt = check_element_visibility_and_return_text(driver, (By.XPATH, "(//span[@class= 'nb-jobs-found'])[2]"))
        total_jobs = _to_int(total_jobs_txt)
        click_element(driver, (By.XPATH, "(//h2[@class= 'job-title']/parent::a)[1]"))

        while job_count < total_jobs and total_jobs > 0:
            try:
                job_url = driver.current_url
                if job_url in done_urls:
                    if not _click_next(driver):
                        break
                    if loop_count == jobs_per_page:
                        print(f"Page {page_count} processed successfully.")
                        page_count += 1
                        loop_count = 0
                    loop_count += 1
                    job_count += 1
                    continue

                job_title = check_element_visibility_and_return_text(driver, (By.ID, "job-title"))
                job_description = check_element_visibility_and_return_text(driver, (By.CLASS_NAME, "job-offer-edited-content"))
                job_location = check_element_visibility_and_return_text(driver, (By.XPATH, create_xpath_1('job-location')))
                job_work_arrangement = check_element_visibility_and_return_text(driver, (By.XPATH, create_xpath_1('work-arrangement')))
                job_salary_type = check_element_visibility_and_return_text(driver, (By.XPATH, create_xpath_1('job-salary-freelance')))
                experience_required = check_element_visibility_and_return_text(driver, (By.XPATH, create_xpath_1('job-requirements')))
                study_required = check_element_visibility_and_return_text(driver, (By.XPATH, create_xpath_1('job-study-level')))
                required_languages = _safe_language_list(driver)
                similar_offers = _safe_similar_offers(driver)
                other_jobs_by_company = check_element_visibility_and_return_href(driver, (By.XPATH, "//div[@id= 'company-logo-container']/a | //a[text()= 'See more offers']"))
                company_description_url = check_element_visibility_and_return_href(driver, (By.XPATH, "//a[text()= 'Company description']"))

                company_name = company_address = company_website = company_description = ''
                if company_description_url:
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(company_description_url)
                    company_name = check_element_visibility_and_return_text(driver, (By.ID, "office-name-title"))
                    company_address = check_element_visibility_and_return_text(driver, (By.ID, "office-contact"))
                    company_website = check_element_visibility_and_return_href(driver, (By.XPATH, "//p[@id= 'office-contact']/a"))
                    if company_address and company_website:
                        company_address = company_address.replace(urlparse(company_website).netloc, '').strip()
                    if "http:///" in company_address:
                        company_address = company_address.replace("http:///", '').strip()
                    company_description = check_element_visibility_and_return_text(driver, (By.ID, "company-description"))
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

                data = {
                    "Job Title": job_title,
                    "Job URL": job_url,
                    "Job Description": job_description,
                    "Company Name": company_name,
                    "Company Address": company_address,
                    "Company Website": company_website,
                    "Company Description": company_description,
                    "Job Location": job_location,
                    "Work Arrangement": job_work_arrangement,
                    "Salary Type": job_salary_type,
                    "Experience Required": experience_required,
                    "Study Required": study_required,
                    "Required Languages": ', '.join(required_languages),
                    "Other Jobs by Company": other_jobs_by_company,
                    "Similar Offers": ', '.join(similar_offers)
                }

                df = pd.DataFrame([data])
                write_mode = 'a' if os.path.exists(output_file_name) else 'w'
                df.to_csv(output_file_name, mode=write_mode, header=write_mode == 'w',
                          index=False, encoding='utf-8-sig', lineterminator='\n')

                with open('done.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{job_url}\n")
                done_urls.add(job_url)
                print(f"Saved: {job_title}")

            except Exception as job_err:
                print(f"Error processing job: {job_err}")

            if not _click_next(driver):
                print("No more pages to process.")
                break

            if loop_count == jobs_per_page:
                print(f"Page {page_count} processed successfully.")
                page_count += 1
                loop_count = 0
            loop_count += 1
            job_count += 1

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Exiting the program.")
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
