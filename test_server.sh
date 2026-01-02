#!/bin/bash 
# Test if BizPulse24.com is working 
echo "🧪 Testing BizPulse24.com..." 
curl -s -o /dev/null -w "%{http_code}" https://bizpulse24.com 
echo "" 
curl -s -o /dev/null -w "%{http_code}" https://bizpulse24.com/mobile 
echo "" 
