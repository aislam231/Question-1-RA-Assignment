# Question-1-RA-Assignment
## Searching and Ranking Methodology

The file [`Searching and ranking methodology.pdf`](Searching%20and%20ranking%20methodology.pdf) presents the complete methodology used to search for, collect, and rank startup incubators in India.

### Contents
- **Data Search and Collection:** The approach used to identify startup incubators and collect relevant information.
- **Selection of Indicators:** The four indicators used to evaluate incubators: Total Startups Incubated, Startups Graduated, Active Startups, and Total Funding Raised.
- **Ranking Methodologies:** Detailed explanations and justifications for:
  1. Borda Count.
  2. CRITIC-based Multi-Criteria Decision Analysis (CRITIC-MCDA).
- **Results:** The top 20 startup incubators identified separately using each ranking methodology.

The report was prepared in LaTeX using Overleaf and compiled into PDF format.

## CRITIC-Based Top 20 Incubator Spreadsheet

The file [`critic_top20_all_features.xlsx`](critic_top20_all_features.xlsx) contains the consolidated spreadsheet of the top 20 startup incubators in India, identified using the CRITIC-based Multi-Criteria Decision Analysis (CRITIC-MCDA) methodology.

The spreadsheet was prepared by joining information from multiple CSV files to bring together the ranking results and the available details of each selected incubator in a single, organized dataset.

It includes the CRITIC-based rankings and scores, website links, basic incubator information, and other collected features available in the source datasets. The spreadsheet provides a comprehensive overview of the selected incubators and facilitates further examination of their characteristics.

## Python Automation Code for Website Scraping

The Jupyter Notebook [`python automation code.ipynb`](python%20automation%20code.ipynb) contains the annotated Python automation code developed to collect the current and archived webpages of the top 20 startup incubators.

### Pages Collected
For each incubator, the automation aims to collect:
- **Homepage:** The incubator's main website page.
- **About Us Page:** The page providing information about the incubator, discovered automatically where possible.

### Webpage Archiving Frequency
The automation searches for the **earliest available webpage capture in each month**, covering the period from **January 2022 to September 2026**, approximately five years.

The collection includes:
- Current versions of the homepage and About Us page.
- Archived versions of these pages for all months in the specified period for which suitable captures are available.

The script organizes the collected HTML files into separate folders for each incubator, keeping current webpages and archived captures separate. This facilitates systematic examination of website content over time.

**Note:** Archived captures may not be available for every month or every webpage. The automation records these gaps rather than assuming that a webpage exists for every month.
## Scraped HTML Files and Collection History

The folder [`scraped_html_top20`](scraped_html_top20/) contains the HTML files collected by the Python automation script for the top 20 startup incubators.

It includes:

- **Current Homepage Files:** The downloaded HTML files of the incubators' current homepages.
- **Current About Us Pages:** The downloaded HTML files of the About Us pages, wherever successfully identified and collected.
- **Archived HTML Files:** Available archived versions of the homepage and About Us pages, organized by incubator, year, and month, covering January 2022 to September 2026.
- **Scraping History and Reports:** Records of the scraping process, including successful downloads, unavailable monthly archive captures, and failed operations, where recorded.

The folder structure keeps the collected webpages organized by incubator and separates current pages from archived versions. This makes it easier to inspect website content and examine how it has changed over time.

**Note-1:** The availability of archived HTML files varies by incubator, webpage, and month. Missing captures indicate that a suitable archived version was not found or collected for that period.
**Note-2:** Since the `scraped_html_top20` folder contains a large number of HTML files and occupies substantial storage space, the complete folder has been uploaded to the GitHub repository directly through Visual Studio Code (VS Code).
