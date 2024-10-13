from scholarly import scholarly
import pandas as pd
import matplotlib.pyplot as plt
import time, random, os, sys

#os.system('pip3 install scholarly pandas matplotlib openpyxl --break-system-packages')

def filtering(pub_bib, keyword, pub_exclude_list):
    meets_criteria = False

    keyword_found = False
    pub_year = False
    pub_venue = True
    pub_author = False 

    if keyword.lower() in pub_bib['title'].lower():
        keyword_found = True
        print(keyword, ' found in the title.')
    if keyword.lower() in pub_bib['abstract'].lower():
        keyword_found = True
        print(keyword, ' found in the abstract.')  

    if is_author_in_pub_bib(keyword, pub_bib):
        print('Author found in the publication.')
        keyword_found = True
        pub_author = True

    try:
        if isinstance(int(pub_bib['year']), int) and len(pub_bib['year']) == 4:
            pub_year = True
            print('Publication year exists:', pub_bib['year'])
    except (ValueError, TypeError):
        pub_year = False
        print('Invalid or missing publication year:', pub_bib['year'])

    # Exclude publications from block list
    if pub_bib['venue'] in pub_exclude_list:
        pub_venue = False
        print('Venue in excluded list', pub_bib['venue'], ' exlcuding publication.')
    #elif pub_bib['venue'] == 'NA':
    #    pub_venue = False
    #    print('Venue is NA, excluding publication.')
    
    if keyword_found and pub_year and pub_venue:
        meets_criteria = True
        print('Publication meets the criteria.')
    else:
        print('Publication does not meet the criteria.')
    return meets_criteria 

def create_excel_with_headers(filename):
    """Create an Excel file with headers if it doesn't already exist."""
    try:
        pd.read_excel(filename)  # Check if the file exists
    except FileNotFoundError:
        # Create an empty DataFrame with the correct structure
        columns = ['Year', 'Authors', 'Title', 'Abstract', 'Publication', 'Citations']
        empty_df = pd.DataFrame(columns=columns)
        empty_df.to_excel(filename, index=False)
        print(f'{filename} created with headers.')

def is_author_in_pub_bib(full_name, pub_bib):
    """Check if the given full name is listed as an author in pub_bib['authors']."""
    # Split the full name into parts
    name_parts = full_name.lower().split()
    
    # Get the list of authors from pub_bib
    authors = pub_bib.get('authors', '').lower()
    # Generate variations of the author's name
    name_variations = [full_name]
    name_parts = full_name.split()
    if len(name_parts) == 2:
        initials = name_parts[0][0] + '. ' + name_parts[1]
        initials_no_dot = name_parts[0][0] + ' ' + name_parts[1]
        name_variations.extend([initials, initials_no_dot])
        print('Author full name is the keyword; name variations include', name_variations)
    # Check if any variation of the author's name exists in pub_bib['authors']
    for variation in name_variations:
        if variation.lower() in authors:
            return True
    
    return False

def is_duplicate_entry(new_entry, reference_df):
    """Check if the new entry is a duplicate based on year, authors, title, and venue."""
    # Ensure the comparison is case-insensitive and data types match
    duplicate = reference_df[
        (reference_df['Year'].astype(str) == str(new_entry['year'])) &
        (reference_df['Title'].str.lower() == new_entry['title'].lower()) &
        (reference_df['Publication'].str.lower() == new_entry['venue'].lower()) &
        (reference_df['Authors'].str.lower() == new_entry['authors'].lower())
    ]
    
    if not duplicate.empty:
        print("Duplicate found:")
        print(duplicate)
    else:
        print("No duplicate found.")
    
    return not duplicate.empty
        
def write_query_to_file(query, keyword, filename, nBatch, pub_exclude_list):

    to_check_duplicates = False
    if not os.path.exists(filename):
        create_excel_with_headers(filename)
        to_check_duplicates = False
    else:
        reference_df = pd.read_excel(filename)
        print(f'{filename} loaded for reference.')
        to_check_duplicates = not reference_df.empty


    nPerBatch = 20
    sleepTime = random.uniform(5, 10)

    for ib in range(nBatch):
        data = {
            'Year': [],
            'Authors': [],
            'Title': [],
            'Abstract': [],
            'Publication': [],
            'Citations': []    
        }   

        nTmp = 0
        print('Processing the ',ib,' batch')
        print(' ')
        for pub in query:
            nTmp += 1
            print('Fetching metadata for the ',ib*nPerBatch+nTmp, ' publications ...')
            bib = pub['bib']
            print(bib)
            print(' ')
            
            title = bib.get('title', 'NA')
            authors = ', '.join(bib.get('author', []))
            abstract = bib.get('abstract', 'NA')
            publication = bib.get('venue', 'NA')
            year = bib.get('pub_year', 'NA')
            citations = pub['num_citations']

            pub_bib = {'title': title,
                       'authors': authors,
                       'abstract': abstract,
                       'year': year,
                       'venue': publication}

            if to_check_duplicates:
                duplicate = is_duplicate_entry(pub_bib, reference_df)
                if duplicate:
                    print(' ')
                else:
                    meets_criteria = filtering(pub_bib, keyword, pub_exclude_list)
                    if meets_criteria:
                        data['Year'].append(year)
                        data['Authors'].append(authors)
                        data['Title'].append(title)
                        data['Abstract'].append(abstract) 
                        data['Publication'].append(publication)
                        data['Citations'].append(citations)
            elif not to_check_duplicates:
                meets_criteria = filtering(pub_bib, keyword, pub_exclude_list)
                if meets_criteria:
                    data['Year'].append(year)
                    data['Authors'].append(authors)
                    data['Title'].append(title)
                    data['Abstract'].append(abstract) 
                    data['Publication'].append(publication)
                    data['Citations'].append(citations)

            time.sleep(sleepTime) 
            if nTmp == nPerBatch:
                break

        # delay between batches
        #time.sleep(sleepTime*3)    
        
        df = pd.DataFrame(data)
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
        df.sort_values(by='Year', ascending=False, inplace=True)

        with pd.ExcelWriter(filename, mode='a', if_sheet_exists='overlay', engine='openpyxl') as writer:
            df.to_excel(writer, index=False, header=True)  # Append without headers
            if os.path.exists(filename):
                existing_df = pd.read_excel(filename)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.sort_values(by='Year', ascending=False, inplace=True)
                combined_df.to_excel(writer, index=False, header=True)
            else:
                df.to_excel(writer, index=False, header=True)

def plot_from_excel(filename, keyword):
    """Load data from Excel and generate plots for article counts and total citations."""
    try:
        # Load data from the Excel file
        df = pd.read_excel(filename)
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return

    if df.empty:
        print("Error: No data available in the Excel file.")
        return

    # Ensure 'Year' is numeric and drop invalid entries
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df.dropna(subset=['Year'], inplace=True)

    # Group by year to compute total citations and article count
    year_counts = df.groupby('Year').agg(
        Total_Citations=('Citations', 'sum'),
        Article_Count=('Title', 'count')
    ).reset_index()

    print(year_counts)  # Optional: Show the year counts summary

    # Create a complete range of years for the x-axis
    all_years = range(int(year_counts['Year'].min()), int(year_counts['Year'].max()) + 1)
    all_years_counts = year_counts.set_index('Year').reindex(all_years, fill_value=0).reset_index()
    all_years_counts.columns = ['Year', 'Total_Citations', 'Article_Count']

    # Create subplots for the two metrics
    fig, ax = plt.subplots(2, 1, figsize=(7, 5), sharex=True)

    # Plot total citations
    ax[0].bar(all_years_counts['Year'], all_years_counts['Total_Citations'], 
              color='blue', alpha=0.6, label='Total Citations')
    ax[0].set_xlabel('Year')
    ax[0].set_ylabel('Total Citations', color='blue')
    ax[0].tick_params(axis='y', labelcolor='blue')
    ax[0].set_title('Total Citations for Publications with ' + keyword)

    # Plot article counts
    ax[1].bar(all_years_counts['Year'], all_years_counts['Article_Count'], 
              color='orange', alpha=0.6, label='Article Count')
    ax[1].set_xlabel('Year')
    ax[1].set_ylabel('Article Count', color='orange')
    ax[1].tick_params(axis='y', labelcolor='orange')
    ax[1].set_title('Number of Articles per Year')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Adjust layout and save the plot as an image
    fig.tight_layout()
    plt.savefig('gmtsar_citations_and_counts_histogram.png')
    plt.show()  # Display the plot
    def is_bib_in_database(bib, filename):
        """Check if the bib entry is already in the Excel database."""
        try:
            df = pd.read_excel(filename)
        except FileNotFoundError:
            return False

        # Check if the title and year match any entry in the database
        existing_entries = df[(df['Title'] == bib['title']) & (df['Year'] == bib['year'])]
        return not existing_entries.empty
    
def print_help():
    help_text = """
    Usage: python3 getCitations.py [option] [keyword] [nBatch]
    
    Options:
    h   Print this help message
    q   Perform query and write results to file, then plot
    p   Plot from existing Excel file
    a   Archive the existing Excel file
    
    Keyword:
    The keyword to search for in the publications.
    
    nBatch (optional):
    The number of batches to process. Default is 1.
    """
    print(help_text)

if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Error: Incorrect number of arguments.")
        print_help()
        sys.exit(1)

    option = sys.argv[1]
    keyword = sys.argv[2]
    filename = keyword + '.publication.database.xlsx'
    nBatch = int(sys.argv[3]) if len(sys.argv) == 4 else 1

    pub_exclude_list = ['AGU Fall Meeting Abstracts']

    if option == 'h':
        print_help()
    elif option == 'q':
        query = scholarly.search_pubs(keyword)
        write_query_to_file(query, keyword, filename, nBatch, pub_exclude_list)
        plot_from_excel(filename, keyword)
    elif option == 'p':
        plot_from_excel(filename, keyword)
    elif option == 'a':
        os.system('cp '+filename + ' '+filename+'.archive.xlsx')
    else:
        print("Error: Unknown option.")
        print_help()
        sys.exit(1)
