import { NextResponse } from 'next/server';

// Updated to use port 5001 which is the correct port for the backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001';

// Helper function to handle API requests
async function fetchFromAPI(endpoint: string, options: RequestInit = {}) {
  // Ensure endpoint doesn't start with a slash if API_BASE_URL ends with one
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint.substring(1) : endpoint;
  const url = `${API_BASE_URL}/${normalizedEndpoint}`;
  
  console.log(`Making API request to: ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    console.log(`API response status: ${response.status} ${response.statusText}`);
    
    // Check if response is empty before parsing JSON
    const text = await response.text();
    
    if (!response.ok) {
      console.error(`API error (${response.status}): ${text}`);
      // Try to parse the error message if possible
      try {
        const errorData = text.length ? JSON.parse(text) : {};
        throw new Error(errorData.message || errorData.error || `API error: ${response.status} ${response.statusText}`);
      } catch (parseError) {
        // If we can't parse the error as JSON, return the text or status
        throw new Error(text || `API error: ${response.status} ${response.statusText}`);
      }
    }
    
    // Parse successful response
    const data = text.length ? JSON.parse(text) : {};
    return data;
  } catch (error) {
    console.error(`API request failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    // Error passed to caller
    throw error;
  }
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get('endpoint');
  
  if (!endpoint) {
    return NextResponse.json({ error: 'Endpoint parameter is required' }, { status: 400 });
  }
  
  try {
    const data = await fetchFromAPI(endpoint);
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function POST(request: Request) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get('endpoint');
  
  if (!endpoint) {
    return NextResponse.json({ error: 'Endpoint parameter is required' }, { status: 400 });
  }
  
  try {
    const body = await request.json();
    const data = await fetchFromAPI(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function PUT(request: Request) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get('endpoint');
  
  if (!endpoint) {
    return NextResponse.json({ error: 'Endpoint parameter is required' }, { status: 400 });
  }
  
  try {
    const body = await request.json();
    const data = await fetchFromAPI(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const endpoint = searchParams.get('endpoint');
  
  if (!endpoint) {
    return NextResponse.json({ error: 'Endpoint parameter is required' }, { status: 400 });
  }
  
  try {
    const data = await fetchFromAPI(endpoint, {
      method: 'DELETE',
    });
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
} 