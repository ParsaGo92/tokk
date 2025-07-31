const _a1b2c3 = (() => {
    const _x9y8z7 = new Uint8Array([0x8f, 0x3d, 0x7a, 0x1e, 0x9c, 0x4b, 0x2f, 0x6e]);
    const _m5n6p7 = new Uint8Array([0x3a, 0x8d, 0x1f, 0x7c, 0x9e, 0x4a, 0x2b, 0x6f]);
    
    const _k8l9m0 = (str, key) => {
        const _q1w2e3 = new TextEncoder();
        const _r4t5y6 = _q1w2e3.encode(str);
        const _u7i8o9 = new Uint8Array(_r4t5y6.length);
        
        for (let i = 0; i < _r4t5y6.length; i++) {
            _u7i8o9[i] = _r4t5y6[i] ^ key[i % key.length];
        }
        return _u7i8o9;
    };
    
    const _p0a1s2 = (data, key) => {
        const _s3w4o5 = new TextDecoder();
        const _r6d7e8 = new Uint8Array(data.length);
        
        for (let i = 0; i < data.length; i++) {
            _r6d7e8[i] = data[i] ^ key[i % key.length];
        }
        return _s3w4o5.decode(_r6d7e8);
    };
    
    return { _k8l9m0, _p0a1s2, _x9y8z7, _m5n6p7 };
})();

const _v1e2r3 = (() => {
    let _s4i5o6 = 0;
    const _n7u8m9 = () => {
        _s4i5o6 = (_s4i5o6 * 0x19660d + 0x3c6ef35f) & 0xffffffff;
        return _s4i5o6 / 0x100000000;
    };
    
    const _b0e1t2 = (min, max) => {
        return Math.floor(_n7u8m9() * (max - min + 1)) + min;
    };
    
    return { _n7u8m9, _b0e1t2 };
})();

const _c4h5e6 = (() => {
    const _c7h8e9 = new Map();
    
    const _s0e1t2 = (key, value) => {
        _c7h8e9.set(key, value);
    };
    
    const _g3e4t5 = (key) => {
        return _c7h8e9.get(key);
    };
    
    return { _s0e1t2, _g3e4t5 };
})();

const _a7n8t9 = (() => {
    const _d0e1t2 = () => {
        const _s3t4a5 = performance.now();
        const _d6e7l8 = _v1e2r3._b0e1t2(10, 50);
        
        return new Promise(resolve => {
            setTimeout(() => {
                const _e9l0a1 = performance.now() - _s3t4a5;
                resolve(_e9l0a1 > _d6e7l8 * 0.8);
            }, _d6e7l8);
        });
    };
    
    const _d2e3b4 = () => {
        try {
            const _e5r6r7 = new Error();
            const _s8t9a0 = _e5r6r7.stack;
            return _s8t9a0.includes('debugger') || _s8t9a0.includes('inspector');
        } catch {
            return false;
        }
    };
    
    const _s1a2n3 = () => {
        const _u4s5e6 = navigator.userAgent.toLowerCase();
        const _a7r8t9 = ['phantom', 'headless', 'selenium', 'webdriver'];
        return _a7r8t9.some(_t0o1o2 => _u4s5e6.includes(_t0o1o2));
    };
    
    return { _d0e1t2, _d2e3b4, _s1a2n3 };
})();

const _i4n5t6 = (() => {
    const _v7e8r9 = async () => {
        const _t0i1m2 = await _a7n8t9._d0e1t2();
        const _d3e4b5 = _a7n8t9._d2e3b4();
        const _s6a7n8 = _a7n8t9._s1a2n3();
        
        if (_t0i1m2 || _d3e4b5 || _s6a7n8) {
            throw new Error(_a1b2c3._p0a1s2(_a1b2c3._x9y8z7, _a1b2c3._m5n6p7));
        }
        
        return true;
    };
    
    return { _v7e8r9 };
})();

const _w0e1a2 = (() => {
    const _k3m4a5 = new WeakMap();
    
    const _s6e7t8 = (obj) => {
        const _i9d0 = _v1e2r3._b0e1t2(1000, 9999);
        _k3m4a5.set(obj, _i9d0);
        return _i9d0;
    };
    
    const _g1e2t3 = (obj) => {
        return _k3m4a5.get(obj);
    };
    
    return { _s6e7t8, _g1e2t3 };
})();

const _v1r2t3 = (() => {
    const _f4n5s6 = new Map();
    let _c7o8u9 = 0;
    
    const _r0e1g2 = (fn) => {
        const _i3d4 = _c7o8u9++;
        _f4n5s6.set(_i3d4, fn);
        return _i3d4;
    };
    
    const _e5x6e7 = (id) => {
        return _f4n5s6.get(id);
    };
    
    return { _r0e1g2, _e5x6e7 };
})();

const _t4s5k6 = (() => {
    const _q7u8e9 = [];
    let _i0d1 = 0;
    
    const _a2d3d4 = (task) => {
        const _i5d6 = _i0d1++;
        _q7u8e9.push({ id: _i5d6, task, executed: false });
        return _i5d6;
    };
    
    const _e7x8e9 = async () => {
        const _r0n1d2 = _v1e2r3._b0e1t2(0, _q7u8e9.length - 1);
        const _t3s4k5 = _q7u8e9[_r0n1d2];
        
        if (_t3s4k5 && !_t3s4k5.executed) {
            _t3s4k5.executed = true;
            await _t3s4k5.task();
        }
    };
    
    return { _a2d3d4, _e7x8e9 };
})();

const _s0t1o2 = (() => {
    const _m3a4p5 = new Map();
    
    const _s6e7t8 = (key, value) => {
        _m3a4p5.set(_w0e1a2._s6e7t8({}), value);
    };
    
    const _g9e0t1 = (key) => {
        for (const [k, v] of _m3a4p5.entries()) {
            if (_w0e1a2._g1e2t3(k) === key) {
                return v;
            }
        }
        return null;
    };
    
    return { _s6e7t8, _g9e0t1 };
})();

const _e2v3e4 = (() => {
    const _h5a6n7 = [];
    
    const _a8d9d0 = (fn) => {
        _h5a6n7.push(fn);
    };
    
    const _e1x2e3 = async () => {
        const _t4a5s6 = [..._h5a6n7];
        _h5a6n7.length = 0;
        
        for (const _f7n8 of _t4a5s6) {
            try {
                await _f7n8();
                await new Promise(resolve => setTimeout(resolve, _v1e2r3._b0e1t2(5, 25)));
            } catch (_e9r0) {
                // Silent error handling
            }
        }
    };
    
    return { _a8d9d0, _e1x2e3 };
})();

const _s1t2a3 = (() => {
    const _s4e5t6 = new Set();
    
    const _a7d8d9 = (id) => {
        _s4e5t6.add(id);
    };
    
    const _h0a1s2 = (id) => {
        return _s4e5t6.has(id);
    };
    
    const _c3l4e5 = () => {
        _s4e5t6.clear();
    };
    
    return { _a7d8d9, _h0a1s2, _c3l4e5 };
})();

const _m4a5i6 = (() => {
    const _i7n8i9 = async () => {
        try {
            await _i4n5t6._v7e8r9();
            
            const _t0a1s2k3 = _t4s5k6._a2d3d4(async () => {
                await new Promise(resolve => setTimeout(resolve, _v1e2r3._b0e1t2(100, 500)));
            });
            
            await _t4s5k6._e7x8e9();
            
            _e2v3e4._a8d9d0(async () => {
                await new Promise(resolve => setTimeout(resolve, _v1e2r3._b0e1t2(50, 200)));
            });
            
            await _e2v3e4._e1x2e3();
            
            return true;
        } catch (_e4r5r6) {
            return false;
        }
    };
    
    return { _i7n8i9 };
})();

export { 
    _m4a5i6, _i4n5t6, _c4h5e6, _w0e1a2, _a1b2c3, _v1e2r3, 
    _v1r2t3, _t4s5k6, _s0t1o2, _e2v3e4, _s1t2a3 
};