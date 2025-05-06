import { NextResponse } from 'next/server';

// The discovery endpoints are on port 8000 based on the working curl test
const DISCOVERY_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001';

export async function GET(request: Request) {
  // Get the requested path from the URL
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get('endpoint');
  
  if (!endpoint) {
    return NextResponse.json({ error: 'Missing endpoint parameter' }, { status: 400 });
  }
  
  // Only allow specific discovery endpoints
  const allowedEndpoints = ['.well-known/openid-configuration', '.well-known/jwks.json'];
  if (!allowedEndpoints.includes(endpoint)) {
    return NextResponse.json({ error: 'Invalid discovery endpoint' }, { status: 400 });
  }
  
  try {
    console.log(`Discovery proxy: Fetching ${endpoint} from ${DISCOVERY_URL}`);
    
    const response = await fetch(`${DISCOVERY_URL}/${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    console.error(`Discovery proxy error:`, error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' }, 
      { status: 500 }
    );
  }
}
