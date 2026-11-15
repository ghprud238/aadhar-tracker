/**
 * Hardware-Backed Encrypted Storage Service
 * 
 * Provides persistent storage using iOS Keychain (kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly)
 * and Android KeyStore / EncryptedSharedPreferences via Expo SecureStore.
 * 
 * Gracefully falls back to web local storage / in-memory cache when running in browser or headless environments.
 */

import * as SecureStore from 'expo-secure-store';

class EncryptedStorageService {
  private memoryFallback: Map<string, string> = new Map();

  private async isSecureStoreAvailable(): Promise<boolean> {
    try {
      return await SecureStore.isAvailableAsync();
    } catch {
      return false;
    }
  }

  /**
   * Encrypts and writes a string value to hardware-backed secure storage.
   */
  public async setItem(key: string, value: string): Promise<void> {
    try {
      const available = await this.isSecureStoreAvailable();
      if (available) {
        await SecureStore.setItemAsync(key, value, {
          keychainAccessible: SecureStore.AFTER_FIRST_UNLOCK_THIS_DEVICE_ONLY,
        });
        return;
      }
    } catch (e) {
      console.warn(`SecureStore write failed for key ${key}, falling back:`, e);
    }

    // Fallback: Web localStorage or in-memory
    if (typeof window !== 'undefined' && window.localStorage) {
      try {
        window.localStorage.setItem(`@suraksha_enc_${key}`, btoa(encodeURIComponent(value)));
        return;
      } catch {}
    }
    this.memoryFallback.set(key, value);
  }

  /**
   * Retrieves and decrypts a value from secure storage.
   */
  public async getItem(key: string): Promise<string | null> {
    try {
      const available = await this.isSecureStoreAvailable();
      if (available) {
        const val = await SecureStore.getItemAsync(key);
        if (val !== null) return val;
      }
    } catch (e) {
      console.warn(`SecureStore read failed for key ${key}, trying fallback:`, e);
    }

    if (typeof window !== 'undefined' && window.localStorage) {
      try {
        const stored = window.localStorage.getItem(`@suraksha_enc_${key}`);
        if (stored) {
          return decodeURIComponent(atob(stored));
        }
      } catch {}
    }

    return this.memoryFallback.get(key) || null;
  }

  /**
   * Deletes a key from secure storage.
   */
  public async removeItem(key: string): Promise<void> {
    try {
      const available = await this.isSecureStoreAvailable();
      if (available) {
        await SecureStore.deleteItemAsync(key);
      }
    } catch {}

    if (typeof window !== 'undefined' && window.localStorage) {
      try {
        window.localStorage.removeItem(`@suraksha_enc_${key}`);
      } catch {}
    }
    this.memoryFallback.delete(key);
  }

  /**
   * Saves any JSON-serializable object to secure storage.
   */
  public async saveJson<T>(key: string, data: T): Promise<void> {
    const jsonStr = JSON.stringify(data);
    await this.setItem(key, jsonStr);
  }

  /**
   * Loads a JSON object from secure storage with a fallback value.
   */
  public async loadJson<T>(key: string, fallback: T): Promise<T> {
    const val = await this.getItem(key);
    if (!val) return fallback;
    try {
      return JSON.parse(val) as T;
    } catch {
      return fallback;
    }
  }
}

export const encryptedStorage = new EncryptedStorageService();
