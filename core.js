const _0x4f2a = (() => {
    const _0x1a3b = new Uint8Array([0x8f, 0x3d, 0x7a, 0x1e, 0x9c, 0x4b, 0x2f, 0x6e]);
    const _0x5c7d = new Uint8Array([0x3a, 0x8d, 0x1f, 0x7c, 0x9e, 0x4a, 0x2b, 0x6f]);
    
    const _0x8e1f = (str, key) => {
        const _0x9a2b = new TextEncoder();
        const _0x7c4d = _0x9a2b.encode(str);
        const _0x3e5f = new Uint8Array(_0x7c4d.length);
        
        for (let i = 0; i < _0x7c4d.length; i++) {
            _0x3e5f[i] = _0x7c4d[i] ^ key[i % key.length];
        }
        return _0x3e5f;
    };
    
    const _0x6b4a = (data, key) => {
        const _0x2d8c = new TextDecoder();
        const _0x4f7e = new Uint8Array(data.length);
        
        for (let i = 0; i < data.length; i++) {
            _0x4f7e[i] = data[i] ^ key[i % key.length];
        }
        return _0x2d8c.decode(_0x4f7e);
    };
    
    return { _0x8e1f, _0x6b4a, _0x1a3b, _0x5c7d };
})();

const _0x7d3f = (() => {
    let _0x9c2a = 0;
    const _0x4e1b = () => {
        _0x9c2a = (_0x9c2a * 0x19660d + 0x3c6ef35f) & 0xffffffff;
        return _0x9c2a / 0x100000000;
    };
    
    const _0x8f4d = (min, max) => {
        return Math.floor(_0x4e1b() * (max - min + 1)) + min;
    };
    
    return { _0x4e1b, _0x8f4d };
})();

const _0x6a4c = (() => {
    const _0x3d8f = new Map();
    
    const _0x7e2a = (key, value) => {
        _0x3d8f.set(key, value);
    };
    
    const _0x9b4c = (key) => {
        return _0x3d8f.get(key);
    };
    
    return { _0x7e2a, _0x9b4c };
})();

const _0x5d3e = (() => {
    const _0x8c1f = () => {
        const _0x4a7d = performance.now();
        const _0x2e5b = _0x7d3f._0x8f4d(10, 50);
        
        return new Promise(resolve => {
            setTimeout(() => {
                const _0x6f8a = performance.now() - _0x4a7d;
                resolve(_0x6f8a > _0x2e5b * 0.8);
            }, _0x2e5b);
        });
    };
    
    const _0x1c9a = () => {
        try {
            const _0x3b4e = new Error();
            const _0x7d2f = _0x3b4e.stack;
            return _0x7d2f.includes('debugger') || _0x7d2f.includes('inspector');
        } catch {
            return false;
        }
    };
    
    const _0x9e4b = () => {
        const _0x2c7d = navigator.userAgent.toLowerCase();
        const _0x5a8f = ['phantom', 'headless', 'selenium', 'webdriver'];
        return _0x5a8f.some(_0x4e1c => _0x2c7d.includes(_0x4e1c));
    };
    
    return { _0x8c1f, _0x1c9a, _0x9e4b };
})();

const _0x4b2d = (() => {
    const _0x6e8f = async () => {
        const _0x3a4c = await _0x5d3e._0x8c1f();
        const _0x7b2e = _0x5d3e._0x1c9a();
        const _0x9c4a = _0x5d3e._0x9e4b();
        
        if (_0x3a4c || _0x7b2e || _0x9c4a) {
            throw new Error(_0x6b4a(_0x4f2a._0x1a3b, _0x4f2a._0x5c7d));
        }
        
        return true;
    };
    
    return { _0x6e8f };
})();

const _0x8d1e = (() => {
    const _0x4c7a = new WeakMap();
    
    const _0x2e5b = (obj) => {
        const _0x7f4a = _0x7d3f._0x8f4d(1000, 9999);
        _0x4c7a.set(obj, _0x7f4a);
        return _0x7f4a;
    };
    
    const _0x9b3c = (obj) => {
        return _0x4c7a.get(obj);
    };
    
    return { _0x2e5b, _0x9b3c };
})();

export { _0x4b2d, _0x6a4c, _0x8d1e, _0x4f2a, _0x7d3f };