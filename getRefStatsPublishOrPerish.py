
import pandas as pd
import sys
from datetime import datetime
import matplotlib.pyplot as plt

def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

def process_data(df, keyword, exclude_source, highlight_source):    
    # Ensure the 'Year' column is integer for sorting
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['Year'])
    df['Year'] = df['Year'].astype(int)

    # Filter rows where 'Title', 'Authors', or 'Abstract' contains the keyword
    filtered_df = df[df[['Title', 'Authors', 'Abstract']].apply(lambda x: x.str.contains(keyword, case=False, na=False)).any(axis=1)]

    # Exclude rows based on journal names
    filtered_df = filtered_df[~filtered_df['Source'].str.contains('|'.join(exclude_source), case=False, na=False)]

    # Add a 'Highlight' column for journals in the highlight list
    filtered_df['Highlight'] = filtered_df['Source'].apply(lambda x: 'Highlight' if x in highlight_source else '')

    filtered_df.sort_values(by='Year', ascending=False, inplace=True)
    return filtered_df

def save_filtered_data(filtered_df, output_file):
    filtered_df.to_csv(output_file, index=True)

def plot_data(filtered_df, keyword):
    # Group by Year: count the number of articles and sum citations
    articles_by_year = filtered_df.groupby('Year').size()
    highlight_articles_by_year = filtered_df[filtered_df['Highlight'] == 'Highlight'].groupby('Year').size()
    highlight_articles_by_year = highlight_articles_by_year.reindex(articles_by_year.index, fill_value=0)
    print(highlight_articles_by_year)
    citations_by_year = filtered_df.groupby('Year')['Cites'].sum()

    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    # Subplot 1: Number of articles by year
    articles_by_year.plot(ax=ax1, kind='bar', color='skyblue', label='Total Articles')
    highlight_articles_by_year.plot(ax=ax1, kind='bar', color='red', linewidth=2, label='Highlighted Articles')
    ax1.set_title(f'Number of Articles by Year from {keyword}')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Number of Articles')
    ax1.legend()

    # Subplot 2: Total citations by year
    citations_by_year.plot(ax=ax2, kind='bar', color='salmon')
    ax2.set_title('Total Citations by Year')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Total Citations')
    # Adjust layout and save the plot
    plt.tight_layout()
    current_date = datetime.now().strftime('%Y%m%d')
    output_plot_file = f"{keyword}.sorted.reference.{current_date}.png"
    plt.savefig(output_plot_file)
    plt.show()

def main():
    keyword = sys.argv[1]
    file_path = f"{keyword}.csv"
    output_file = f"{keyword}.sorted.reference.{datetime.now().strftime('%Y%m%d')}.csv"

    exclude_source = ['AGU Fall Meeting', 'AGU Fall Meeting Abstracts', 'ArXiv', 'bioRxiv', 'medRxiv', 'ResearchGate', 'Springer', 'Wiley', 'Elsevier', 'IEEE', 'ACM', 'arXiv', 'biorxiv', 'medrxiv', 'researchgate', 'springer', 'wiley', 'elsevier', 'ieee', 'acm']
    highlight_source = ['Nature', 'Science', 'Scientific Reports', 'Nature …', 'Nature Geoscience']
    df = load_data(file_path)
    filtered_df = process_data(df, keyword, exclude_source, highlight_source)
    save_filtered_data(filtered_df, output_file)
    plot_data(filtered_df, keyword)

if __name__ == "__main__":
    main()
