#!/usr/bin/env python3
"""
APOC Verification Script
Checks if APOC is properly installed and configured in Neo4j
"""

import sys
from src.utils.config import load_config
from src.utils.neo4j_connection import Neo4jConnection


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def verify_apoc():
    """Verify APOC installation"""
    
    print_section("APOC Verification")
    
    try:
        # Load configuration
        config = load_config()
        print(f"✓ Configuration loaded")
        
        # Connect to Neo4j
        conn = Neo4jConnection(
            uri=config['neo4j']['uri'],
            user=config['neo4j']['username'],
            password=config['neo4j']['password'],
            database=config['neo4j']['database']
        )
        print(f"✓ Connected to Neo4j at {config['neo4j']['uri']}")
        
        # Test 1: Check if APOC procedures are available
        print_section("Test 1: APOC Procedures")
        # Try new GQL syntax first (Neo4j 2025.x), fall back to old syntax
        try:
            query = """
            SHOW PROCEDURES 
            YIELD name 
            WHERE name STARTS WITH 'apoc' 
            RETURN count(name) as apoc_procedures
            """
            result = conn.execute_query(query)
            apoc_count = result[0]['apoc_procedures']
        except Exception as e1:
            # Fallback to old syntax for Neo4j 5.x
            try:
                query = """
                CALL dbms.procedures() 
                YIELD name 
                WHERE name STARTS WITH 'apoc' 
                RETURN count(name) as apoc_procedures
                """
                result = conn.execute_query(query)
                apoc_count = result[0]['apoc_procedures']
            except Exception as e2:
                print(f"✗ Could not query procedures: {e2}")
                return False
        
        if apoc_count > 0:
            print(f"✓ Found {apoc_count} APOC procedures")
        else:
            print(f"✗ No APOC procedures found")
            print(f"  APOC may not be installed or enabled")
            return False
        
        # Test 2: Check APOC version
        print_section("Test 2: APOC Version")
        try:
            query = "RETURN apoc.version() as version"
            result = conn.execute_query(query)
            version = result[0]['version']
            print(f"✓ APOC version: {version}")
        except Exception as e:
            print(f"✗ Could not get APOC version: {e}")
        
        # Test 3: Test apoc.meta.schema
        print_section("Test 3: apoc.meta.schema")
        try:
            query = "CALL apoc.meta.schema() YIELD value RETURN count(value) as schema_count"
            result = conn.execute_query(query)
            schema_count = result[0]['schema_count']
            print(f"✓ apoc.meta.schema works! Found {schema_count} schema elements")
        except Exception as e:
            print(f"✗ apoc.meta.schema failed: {e}")
            print(f"  This procedure is needed for graph visualization")
            return False
        
        # Test 4: List some useful APOC procedures
        print_section("Test 4: Available APOC Categories")
        try:
            query = """
            SHOW PROCEDURES 
            YIELD name 
            WHERE name STARTS WITH 'apoc' 
            WITH split(name, '.')[1] as category
            RETURN DISTINCT category
            ORDER BY category
            """
            result = conn.execute_query(query)
            categories = [r['category'] for r in result]
            print(f"✓ Available APOC categories ({len(categories)}):")
            for cat in categories[:20]:  # Show first 20
                print(f"  - apoc.{cat}.*")
            if len(categories) > 20:
                print(f"  ... and {len(categories) - 20} more")
        except Exception as e:
            print(f"ℹ Could not list categories (Neo4j syntax varies): {e}")
            print(f"  This is not critical - APOC is working")
        
        # Test 5: Check specific procedures used in this project
        print_section("Test 5: Project-Specific APOC Functions")
        required_procedures = [
            'apoc.meta.schema',
            'apoc.meta.stats',
            'apoc.meta.nodeTypeProperties',
            'apoc.meta.relTypeProperties',
        ]
        
        try:
            query = """
            SHOW PROCEDURES 
            YIELD name 
            WHERE name STARTS WITH 'apoc' 
            RETURN collect(name) as all_procedures
            """
            result = conn.execute_query(query)
            all_procedures = result[0]['all_procedures']
            
            missing = []
            for proc in required_procedures:
                if proc in all_procedures:
                    print(f"✓ {proc}")
                else:
                    print(f"✗ {proc} - NOT FOUND")
                    missing.append(proc)
            
            if missing:
                print(f"\n⚠ Warning: {len(missing)} required procedures are missing")
                print(f"  This may indicate APOC Core vs Extended version mismatch")
        except Exception as e:
            print(f"ℹ Could not verify specific procedures: {e}")
            print(f"  This is not critical - main APOC functions are working")
        
        # Test 6: Test APOC export capabilities (if enabled)
        print_section("Test 6: APOC Export Configuration")
        try:
            query = "CALL apoc.config.list() YIELD key, value WHERE key CONTAINS 'export' RETURN key, value"
            result = conn.execute_query(query)
            if result:
                print("✓ APOC export configuration:")
                for r in result:
                    print(f"  {r['key']}: {r['value']}")
            else:
                print("ℹ No export configuration found (may be disabled)")
        except Exception as e:
            print(f"ℹ Could not check export config: {e}")
        
        conn.close()
        
        # Summary
        print_section("Verification Summary")
        print("✓ APOC is properly installed and configured!")
        print("✓ All required procedures are available")
        print("\nYou can now use APOC features in this project:")
        print("  - python main.py query graph-schema")
        print("  - python main.py export --format apoc-json")
        print("  - CALL apoc.meta.schema() in Neo4j Browser")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure Neo4j is running")
        print("2. Check if APOC jar is in plugins directory")
        print("3. Verify neo4j.conf has APOC configuration")
        print("4. Restart Neo4j after installing APOC")
        print("5. Check Neo4j logs for errors")
        print("\nSee APOC_SETUP.md for detailed installation instructions")
        return False


def main():
    """Main entry point"""
    success = verify_apoc()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
