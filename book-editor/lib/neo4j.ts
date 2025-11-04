import neo4j, { Driver, Session } from 'neo4j-driver';

let driver: Driver | null = null;

export function getDriver(): Driver {
  if (!driver) {
    const uri = process.env.NEO4J_URI || 'bolt://localhost:7687';
    const username = process.env.NEO4J_USERNAME || 'neo4j';
    const password = process.env.NEO4J_PASSWORD || '';
    
    driver = neo4j.driver(uri, neo4j.auth.basic(username, password));
  }
  return driver;
}

export function getSession(): Session {
  const database = process.env.NEO4J_DATABASE || 'neo4j';
  return getDriver().session({ database });
}

export async function closeDriver(): Promise<void> {
  if (driver) {
    await driver.close();
    driver = null;
  }
}
