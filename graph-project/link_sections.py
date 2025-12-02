#!/usr/bin/env python3
"""
Link sections with NEXT and PREVIOUS relationships based on their order within chapters.
Similar to how paragraphs are linked.

Usage:
    python link_sections.py              # Execute changes
    python link_sections.py --dry-run    # Preview changes without applying
"""

import sys
import yaml
import argparse
from pathlib import Path
from neo4j import GraphDatabase

def load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent / "config" / "config.yml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_section_links(driver, dry_run=False):
    """Create NEXT and PREVIOUS relationships between sections within each chapter"""
    
    mode_label = "🔍 DRY RUN MODE" if dry_run else "✏️  EXECUTION MODE"
    print(f"\n{mode_label}\n")
    
    if dry_run:
        print("⚠️  This is a dry run - no changes will be made to the database\n")
    
    with driver.session() as session:
        # First, let's see what we have
        result = session.run("""
            MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
            WHERE s.order IS NOT NULL
            RETURN count(DISTINCT c) as chapters, count(s) as sections
        """)
        stats = result.single()
        print(f"Found {stats['chapters']} chapters with {stats['sections']} sections")
        
        # Check existing NEXT/PREVIOUS relationships between sections
        result = session.run("""
            MATCH (s1:Section)-[r:NEXT|PREVIOUS]->(s2:Section)
            RETURN count(r) as existing
        """)
        existing = result.single()['existing']
        if existing > 0:
            print(f"Found {existing} existing section relationships")
            if not dry_run:
                # Delete existing relationships
                result = session.run("""
                    MATCH (s1:Section)-[r:NEXT|PREVIOUS]->(s2:Section)
                    DELETE r
                    RETURN count(r) as deleted
                """)
                deleted = result.single()['deleted']
                print(f"Deleted {deleted} existing section relationships")
        else:
            print("No existing section relationships found")
        
        if dry_run:
            # Preview what would be created - show all links grouped by chapter
            result = session.run("""
                MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
                WHERE s.order IS NOT NULL
                WITH c, s
                ORDER BY c.id, s.order
                WITH c, collect(s) as sections
                UNWIND range(0, size(sections)-2) as i
                WITH c, sections[i] as s1, sections[i+1] as s2
                RETURN 
                    c.title as chapter_title,
                    s1.order as from_order,
                    s1.title as from_title,
                    s2.order as to_order,
                    s2.title as to_title
                ORDER BY c.title, from_order
            """)
            
            links = result.data()
            if links:
                print(f"\nWould create the following {len(links)} NEXT/PREVIOUS link pairs:\n")
                current_chapter = None
                for link in links:
                    if current_chapter != link['chapter_title']:
                        current_chapter = link['chapter_title']
                        print(f"\n📚 {current_chapter}")
                        print("=" * 80)
                    
                    print(f"  [{link['from_order']:2d}] {link['from_title'][:60]}")
                    print(f"   ↓ NEXT")
                    print(f"  [{link['to_order']:2d}] {link['to_title'][:60]}")
                    print()
            else:
                print("\nNo links would be created")
            
            # Summary
            total_links = len(links)
            print(f"\n{'='*80}")
            print(f"Summary: Would create {total_links} NEXT and {total_links} PREVIOUS relationships")
        else:
            # Create NEXT relationships between sections within each chapter
            # Order sections by their order property within each chapter
            result = session.run("""
                MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
                WHERE s.order IS NOT NULL
                WITH c, s
                ORDER BY c.id, s.order
                WITH c, collect(s) as sections
                UNWIND range(0, size(sections)-2) as i
                WITH sections[i] as s1, sections[i+1] as s2
                MERGE (s1)-[:NEXT]->(s2)
                RETURN count(*) as next_created
            """)
            next_created = result.single()['next_created']
            print(f"Created {next_created} NEXT relationships between sections")
            
            # Create PREVIOUS relationships (reverse of NEXT)
            result = session.run("""
                MATCH (s1:Section)-[:NEXT]->(s2:Section)
                MERGE (s2)-[:PREVIOUS]->(s1)
                RETURN count(*) as prev_created
            """)
            prev_created = result.single()['prev_created']
            print(f"Created {prev_created} PREVIOUS relationships between sections")
        
        # Verify the results
        result = session.run("""
            MATCH (s:Section)
            OPTIONAL MATCH (s)-[:NEXT]->(next:Section)
            OPTIONAL MATCH (s)-[:PREVIOUS]->(prev:Section)
            RETURN 
                count(DISTINCT s) as total_sections,
                count(DISTINCT next) as sections_with_next,
                count(DISTINCT prev) as sections_with_previous
        """)
        verification = result.single()
        print(f"\nVerification:")
        print(f"  Total sections: {verification['total_sections']}")
        print(f"  Sections with NEXT: {verification['sections_with_next']}")
        print(f"  Sections with PREVIOUS: {verification['sections_with_previous']}")
        
        # Show a sample chain from one chapter
        result = session.run("""
            MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
            WHERE s.order IS NOT NULL
            WITH c, s
            ORDER BY c.id, s.order
            LIMIT 1
            MATCH path = (s)-[:NEXT*0..3]->()
            RETURN [node in nodes(path) | {title: node.title, order: node.order}] as chain
            LIMIT 1
        """)
        sample = result.single()
        if sample:
            print(f"\nSample section chain:")
            for node in sample['chain']:
                print(f"  Order {node['order']}: {node['title']}")

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Link sections with NEXT and PREVIOUS relationships',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python link_sections.py              # Execute changes
    python link_sections.py --dry-run    # Preview changes without applying
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
        
        # Create section links
        create_section_links(driver, dry_run=args.dry_run)
        
        if args.dry_run:
            print("\n✅ Dry run completed - no changes were made")
            print("   Run without --dry-run to apply changes")
        else:
            print("\n✅ Section linking completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        driver.close()

if __name__ == "__main__":
    main()
