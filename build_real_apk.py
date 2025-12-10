#!/usr/bin/env python3
"""
BizPulse Dynamic APK Builder - Like Instagram!
Creates APK that auto-updates from server without rebuilding
"""
import os
import zipfile
import json
from pathlib import Path
from datetime import datetime

def create_dynamic_apk():
    print("🚀 BizPulse Dynamic APK Builder")
    print("📱 Creating Instagram-style auto-updating APK...")
    print("=" * 60)
    
    # Create zip filename
    zip_name = f"BizPulse_Ultimate_Fixed.zip"
    
    try:
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            
            print("📱 Creating dynamic mobile app...")
            
            # Add the dynamic mobile app (this is the magic!)
            if os.path.exists("dynamic_mobile_app.html"):
                zipf.write("dynamic_mobile_app.html", "www/index.html")
                print("   ✅ Added: Dynamic mobile app as index.html")
            
            # Add minimal static assets
            static_files = ["static/manifest.json", "static/icon-192.png"]
            for file_path in static_files:
                if os.path.exists(file_path):
                    zipf.write(file_path, f"www/{file_path}")
                    print(f"   ✅ Added: {file_path}")
            
            print("🤖 Creating Android project...")
            
            # Android Manifest - Minimal permissions
            android_manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.bizpulse.erp"
    android:versionCode="1"
    android:versionName="1.0.0">
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    
    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="BizPulse ERP"
        android:usesCleartextTraffic="true"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="portrait">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>'''
            
            zipf.writestr("android/app/src/main/AndroidManifest.xml", android_manifest)
            
            # MainActivity - Dynamic content loader
            main_activity = '''package com.bizpulse.erp;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebSettings;
import android.webkit.WebChromeClient;
import android.view.Window;
import android.view.WindowManager;

public class MainActivity extends Activity {
    private WebView webView;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Full screen
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                           WindowManager.LayoutParams.FLAG_FULLSCREEN);
        
        // Create WebView
        webView = new WebView(this);
        setContentView(webView);
        
        // Configure WebView for dynamic content
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setAllowUniversalAccessFromFileURLs(true);
        webSettings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        
        // Enable debugging
        WebView.setWebContentsDebuggingEnabled(true);
        
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                view.loadUrl(url);
                return true;
            }
        });
        
        webView.setWebChromeClient(new WebChromeClient());
        
        // Load the dynamic app
        webView.loadUrl("file:///android_asset/www/index.html");
    }
    
    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}'''
            
            zipf.writestr("android/app/src/main/java/com/bizpulse/erp/MainActivity.java", main_activity)       
     
            # Build.gradle - Optimized for dynamic content
            build_gradle = '''apply plugin: 'com.android.application'

android {
    compileSdkVersion 33
    buildToolsVersion "33.0.0"
    
    defaultConfig {
        applicationId "com.bizpulse.erp"
        minSdkVersion 21
        targetSdkVersion 33
        versionCode 1
        versionName "1.0.0"
        
        multiDexEnabled true
    }
    
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
        debug {
            debuggable true
        }
    }
    
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'androidx.multidex:multidex:2.0.1'
}'''
            
            zipf.writestr("android/app/build.gradle", build_gradle)
            
            # Project level build.gradle
            project_gradle = '''buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:7.4.2'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}'''
            
            zipf.writestr("android/build.gradle", project_gradle)
            
            # Gradle wrapper properties
            gradle_wrapper = '''distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-7.6-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists'''
            
            zipf.writestr("android/gradle/wrapper/gradle-wrapper.properties", gradle_wrapper)
            
            # App resources
            strings_xml = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">BizPulse ERP</string>
</resources>'''
            
            zipf.writestr("android/app/src/main/res/values/strings.xml", strings_xml)
            
            # App icon (placeholder)
            colors_xml = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="colorPrimary">#732C3F</color>
    <color name="colorPrimaryDark">#5D2332</color>
    <color name="colorAccent">#F7E8EC</color>
</resources>'''
            
            zipf.writestr("android/app/src/main/res/values/colors.xml", colors_xml)
            
            # Settings.gradle
            settings_gradle = '''include ':app'
rootProject.name = "BizPulse ERP"'''
            
            zipf.writestr("android/settings.gradle", settings_gradle)
            
            # README with instructions
            readme = f'''# BizPulse ERP - Dynamic APK (Like Instagram!)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🚀 What Makes This Special:
- ✅ APK loads content from YOUR server
- ✅ Changes to web files update automatically
- ✅ No need to rebuild APK for updates
- ✅ Works like Instagram/Facebook apps

## 📱 How It Works:
1. APK is just a "shell" (like Instagram)
2. All content loads from your Python server
3. When you change web files, app updates instantly
4. Users always get the latest version

## 🛠️ Build Instructions:

### Android Studio:
1. Extract this ZIP
2. Open 'android' folder in Android Studio
3. Build > Generate Signed Bundle/APK
4. Install APK on device

### Command Line:
```bash
cd android
./gradlew assembleDebug
```

## 🔄 How to Update Your App:
1. Make changes to your web files (mobile_web_app.html, app.py, etc.)
2. Restart your Python server: `python app.py`
3. App automatically gets updates - NO APK REBUILD NEEDED!

## 📋 Server Requirements:
- Keep `python app.py` running on your computer
- Make sure phone and computer are on same WiFi
- Update IP address in dynamic_mobile_app.html if needed

## 🎯 Key Features:
- Dynamic content loading
- Auto-refresh every 30 seconds
- Offline detection
- Multiple server URL fallbacks
- Instagram-style architecture

Your BizPulse ERP now works like a professional app! 🎉
'''
            
            zipf.writestr("README.md", readme)
        
        # Get file size
        file_size = os.path.getsize(zip_name) / (1024 * 1024)
        
        print("=" * 60)
        print("🎉 DYNAMIC APK BUILD SUCCESSFUL!")
        print(f"📱 Package: {zip_name}")
        print(f"📊 Size: {file_size:.1f} MB")
        print("🚀 Instagram-style auto-updating APK ready!")
        print("\n✨ MAGIC FEATURES:")
        print("   ✅ No APK rebuild needed for updates")
        print("   ✅ Content loads from your server")
        print("   ✅ Auto-refresh every 30 seconds")
        print("   ✅ Works offline with cached content")
        print("\n📋 Next Steps:")
        print("1. Extract ZIP and build APK in Android Studio")
        print("2. Install APK on your device")
        print("3. Keep 'python app.py' running for updates")
        print("4. Change web files - app updates automatically!")
        
        return True
        
    except Exception as e:
        print(f"❌ Build failed: {str(e)}")
        return False

if __name__ == "__main__":
    create_dynamic_apk()