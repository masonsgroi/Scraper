#!/usr/bin/env python3
"""
Test scraper against live API - quick iteration script
Usage: python3 test_scraper_live.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraper import scrape_lift_data

if __name__ == "__main__":
    print("=" * 70)
    print("TESTING scrape_lift_data() AGAINST LIVE API")
    print("=" * 70)
    print()
    
    try:
        status_df, wait_time_df = scrape_lift_data()
        
        print()
        print("=" * 70)
        print(f"✅ SUCCESS! Scraped {len(status_df)} lifts")
        print("=" * 70)
        print()
        
        # Show status data
        print("STATUS DATA:")
        print("-" * 70)
        print(status_df.to_string(index=False))
        print()
        
        # Show wait time data
        print("WAIT TIME DATA:")
        print("-" * 70)
        print(wait_time_df.to_string(index=False))
        print()
        
        # Summary statistics
        print("=" * 70)
        print("SUMMARY:")
        print("=" * 70)
        print(f"Total lifts: {len(status_df)}")
        
        if 'Status' in status_df.columns:
            status_counts = status_df['Status'].value_counts()
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
        
        # Optionally save to local CSV files for inspection
        status_df.to_csv('status_test.csv', index=False)
        wait_time_df.to_csv('wait_time_test.csv', index=False)
        print()
        print("📁 Saved to status_test.csv and wait_time_test.csv")
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"{e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

