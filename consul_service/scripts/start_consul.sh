#!/bin/bash

echo "Starting Consul in development mode..."
echo "Consul UI will be available at: http://localhost:8500"
echo "Press Ctrl+C to stop Consul"

consul agent -dev 