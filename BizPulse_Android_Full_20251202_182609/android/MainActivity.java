package com.bizpulse.retail;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.webkit.WebChromeClient;
import android.webkit.ConsoleMessage;
import android.util.Log;
import android.content.Intent;
import android.net.Uri;

public class MainActivity extends Activity {
    private WebView webView;
    private static final String TAG = "BizPulse";
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Create WebView
        webView = new WebView(this);
        setContentView(webView);
        
        // Configure WebView settings
        setupWebView();
        
        // Load the app
        loadApp();
    }
    
    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        
        // Enable JavaScript
        settings.setJavaScriptEnabled(true);
        
        // Enable file access (CRITICAL for loading local assets)
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccessFromFileURLs(true);
        settings.setAllowUniversalAccessFromFileURLs(true);
        
        // Enable DOM storage and database
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        
        // Enable app cache
        settings.setAppCacheEnabled(true);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        
        // Allow mixed content (HTTP/HTTPS)
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        
        // Set user agent for better compatibility
        settings.setUserAgentString(settings.getUserAgentString() + " BizPulseApp/1.0");
        
        // Enable zoom controls (optional)
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(false);
        
        // Set WebViewClient to handle page navigation
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Log.e(TAG, "WebView Error: " + errorCode + " - " + description + " URL: " + failingUrl);
                super.onReceivedError(view, errorCode, description, failingUrl);
            }
            
            @Override
            public void onPageFinished(WebView view, String url) {
                Log.d(TAG, "Page loaded successfully: " + url);
                super.onPageFinished(view, url);
            }
            
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                Log.d(TAG, "Loading URL: " + url);
                
                // Handle external links (tel:, mailto:, http:, https:)
                if (url.startsWith("tel:") || url.startsWith("mailto:") || 
                    url.startsWith("http:") || url.startsWith("https:")) {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    startActivity(intent);
                    return true;
                }
                
                // Load internal links in WebView
                return false;
            }
        });
        
        // Set WebChromeClient to handle console messages and alerts
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
                Log.d(TAG, "Console: " + consoleMessage.message() + 
                      " -- From line " + consoleMessage.lineNumber() + 
                      " of " + consoleMessage.sourceId());
                return true;
            }
            
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                Log.d(TAG, "Loading progress: " + newProgress + "%");
                super.onProgressChanged(view, newProgress);
            }
        });
    }
    
    private void loadApp() {
        // Load the main HTML file from assets
        String url = "file:///android_asset/index.html";
        Log.d(TAG, "Loading app from: " + url);
        webView.loadUrl(url);
    }
    
    @Override
    public void onBackPressed() {
        // Handle back button - go back in WebView history if possible
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
    
    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
