#!/usr/bin/env python3
"""
Fix section order by extracting section numbers from titles.

Section titles typically start with a number like "1.", "2.", "10.", etc.
This script extracts those numbers and uses them as the correct order value.

Usage:
    python fix_section_order.py              # Execute changes
    python fix_section_order.py --dry-run    # Preview changes without applying
"""

import sys
import yaml
import argparse
import re
from pathlib import Path
from neo4j import GraphDatabase

def load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent / "config" / "config.yml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def extract_section_number(title):
    """
    Extract section number from title.
    
    Examples:
        "1. Гиперчастотная механика..." -> 1
        "10. Явление рассеяния..." -> 10
        "2. Электрино — вторая..." -> 2
        "Предварительные замечание к главе." -> None
    """
    # Try to match number at the beginning followed by a dot
    match = re.match(r'^(\d+)\.', title)
    if match:
        return int(match.group(1))
    
    # Try to match number at the beginning followed by a space
    match = re.match(r'^(\d+)\s', title)
    if match:
        return int(match.group(1))
    
    return None

def fix_section_order(driver, dry_run=False):
    """Fix section order based on section numbers in titles"""
    
    mode_label = "🔍 DRY RUN MODE" if dry_run else "✏️  EXECUTION MODE"
    print(f"\n{mode_label}\n")
    
    if dry_run:
        print("⚠️  This is a dry run - no changes will be made to the database\n")
    
    with driver.session() as session:
        # Get all sections
        result = session.run("""
            MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
            RETURN 
                c.id as chapter_id,
                c.title as chapter_title,
                s.id as section_id,
                s.title as section_title,
                s.order as current_order
            ORDER BY c.id, s.order
        """)
        
        sections = result.data()
        print(f"Found {len(sections)} sections\n")
        
        # Analyze and prepare updates
        updates = []
        no_number = []
        
        for section in sections:
            section_num = extract_section_number(section['section_title'])
            
            if section_num is not None:
                if section_num != section['current_order']:
                    updates.append({
                        'section_id': section['section_id'],
                        'section_title': section['section_title'],
                        'chapter_title': section['chapter_title'],
                        'old_order': section['current_order'],
                        'new_order': section_num
                    })
            else:
                no_number.append({
                    'section_id': section['section_id'],
                    'section_title': section['section_title'],
                    'chapter_title': section['chapter_title'],
                    'current_order': section['current_order']
                })
        
        # Show sections without numbers
        if no_number:
            print("⚠️  Sections without extractable numbers (will keep current order):\n")
            for s in no_number:
                print(f"  [{s['current_order']:2d}] {s['section_title'][:70]}")
                print(f"      Chapter: {s['chapter_title'][:60]}")
                print()
        
        # Show updates to be made
        if updates:
            print(f"\n{'Will update' if dry_run else 'Updating'} {len(updates)} sections:\n")
            
            current_chapter = None
            for upd in sorted(updates, key=lambda x: (x['chapter_title'], x['new_order'])):
                if current_chapter != upd['chapter_title']:
                    current_chapter = upd['chapter_title']
                    print(f"\n📚 {current_chapter}")
                    print("=" * 80)
                
                print(f"  Order: {upd['old_order']:2d} → {upd['new_order']:2d}")
                print(f"  Title: {upd['section_title'][:70]}")
                print()
            
            if not dry_run:
                # Apply updates
                update_count = 0
                for upd in updates:
                    session.run("""
                        MATCH (s:Section {id: $section_id})
                        SET s.order = $new_order
                    """, section_id=upd['section_id'], new_order=upd['new_order'])
                    update_count += 1
                
                print(f"\n✅ Updated {update_count} sections")
        else:
            print("✅ All sections already have correct order!")
        
        # Show verification
        if not dry_run and updates:
            print("\nVerifying changes...")
            result = session.run("""
                MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
                WHERE s.order IS NOT NULL
                WITH c, s
                ORDER BY c.id, s.order
                RETURN 
                    c.title as chapter_title,
                    collect({order: s.order, title: s.title}) as sections
                LIMIT 3
            """)
            
            print("\nSample of corrected order (first 3 chapters):")
            for record in result:
                print(f"\n📚 {record['chapter_title']}")
                for s in record['sections'][:5]:  # Show first 5 sections
                    print(f"  [{s['order']:2d}] {s['title'][:70]}")
                if len(record['sections']) > 5:
                    print(f"  ... and {len(record['sections']) - 5} more")

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Fix section order based on section numbers in titles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fix_section_order.py              # Execute changes
    python fix_section_order.py --dry-run    # Preview changes without applying
        """
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    neo4j_config = config['neo4j']
    
    # Connect to Neo4j
    print(f"Connecting to Neo4j at {neo4j_config['uri']}...")
    driver = GraphDatabase.driver(
        neo4j_config['uri'],
        auth=(neo4j_config['username'], neo4j_config['password'])
    )
    
    try:
        # Test connection
        driver.verify_connectivity()
        print("Connected successfully!")
        
        # Fix section order
        fix_section_order(driver, dry_run=args.dry_run)
        
        if args.dry_run:
            print("\n✅ Dry run completed - no changes were made")
            print("   Run without --dry-run to apply changes")
        else:
            print("\n✅ Section order fixing completed successfully!")
            print("\n💡 Now you can run: python link_sections.py")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        driver.close()

if __name__ == "__main__":
    main()
