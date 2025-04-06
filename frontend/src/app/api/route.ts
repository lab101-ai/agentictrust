import { NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

// Helper function to handle API requests
async function fetchFromAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}/${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.message || 'An error occurred');
    }
    
    return data;
  } catch (error) {
    console.error(`Error calling ${endpoint}:`, error);
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