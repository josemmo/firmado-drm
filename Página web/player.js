var player = {
	/** Constants **/
	VIDEO_PATH: 'video.mp4',
	WATERMARK_LENGTH: 32,
	SQUARE_SIZE: 3,
	DEMO_MODE: false,

	/**
	 * Initialize player
	 * @param {string} dataToInject
	 */
	initialize: function(dataToInject) {
		var ts = this;
		
		// Convert dataToInject (string) to watermark (int array)
		ts.watermark_pos = 0;
		ts.watermark = [];
		var base64 = btoa(dataToInject);
		base64 = base64.replace(/=/g, ''); // Remove padding character (not needed anymore)
		if (base64.length > ts.WATERMARK_LENGTH) {
			console.error('Data to inject is longer than ' + ts.WATERMARK_LENGTH + ' bytes');
			return false;
		}
		for (var j=0; j<ts.WATERMARK_LENGTH; j++) {
			ts.watermark[j] = (j < base64.length) ? ts.b64ToInt(base64[j]) : 0;
		}
	
		// Get canvas context
		ts.canvas = document.getElementById('player');
		ts.ctx = ts.canvas.getContext('2d');
		
		// Create video object
		ts.video = document.createElement('video');
		ts.video.src = ts.VIDEO_PATH;
		ts.video.loop = true;
		ts.video.oncanplay = function() {
			// Set canvas size to match video dimensions
			ts.canvas.width = ts.video.videoWidth;
			ts.canvas.height = ts.video.videoHeight;
			
			// Resize canvas
			ts.resize();
			window.onresize = function() {
				ts.resize();
			};
			
			// Start rendering frames
			ts.video.play();
			ts.renderFrame();
		};
	},
	
	/**
	 * Base64 to int
	 * @param {string} base64Code
	 * @return {int} code
	 */
	 b64ToInt: function(b64) {
		var dict = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
		return dict.indexOf(b64);
	 },
	
	/**
	 * Resize player
	 */
	resize: function() {
		var ts = this;
		var newWidth = (ts.video.videoWidth * window.innerHeight) / ts.video.videoHeight;
		var newHeight = (ts.video.videoHeight * window.innerWidth) / ts.video.videoWidth;
		if (newWidth > window.innerWidth) {
			ts.canvas.style.cssText = 'width:100%; height:' + newHeight + 'px; top:50%; margin-top:-' + (newHeight/2) + 'px';
		} else {
			ts.canvas.style.cssText = 'height:100%; width:' + newWidth + 'px; left:50%; margin-left:-' + (newWidth/2) + 'px';
		}
		ts.regeneratePixels();
	},
	
	/**
	 * Regenerate square's pixel positions
	 */
	regeneratePixels: function() {
		// Empty pixels array
		this._pixels = [];
		
		// Initialize pointers
		var pointer = this.video.videoWidth * (this.video.videoHeight - 1) * 4;
		var pointer_tag = 0;
		
		// Get square dimension to match, in screen resolution,
		// regardless of video resolution
		var dimension = (this.SQUARE_SIZE * this.video.videoWidth) / window.innerWidth;
		dimension = Math.round(dimension);
		
		// Generate squares of pixels
		for (var i=0; i<dimension; i++) {
			for (var j=0; j<dimension; j++) {
				this._pixels.push([
					pointer_tag + (j*4),    // Tranmission order ID
					pointer + (j*4)         // Tranmission data
				]);
			}
			var x = this.video.videoWidth * 4;
			pointer -= x;
			pointer_tag += x;
		}
	},
	
	/**
	 * Render frame
	 */
	renderFrame: function() {
		var ts = this;
		
		// Draw frame from video
		ts.ctx.drawImage(ts.video, 0, 0);
		
		// Get RGB array and inject watermark
		var img = ts.ctx.getImageData(0, 0, ts.video.videoWidth, ts.video.videoHeight);
		ts.tamperData(img);
		
		// Put new data into canvas
		ts.ctx.putImageData(img, 0, 0);
		
		// Render next frame
		setTimeout(function() {
			ts.renderFrame();
		}, 10);
	},
	
	/**
	 * Tamper frame data
	 * @param {int array} frame
	 **/
	tamperData: function(img) {
		var val = this.watermark[this.watermark_pos];
		for (var i=0; i<this._pixels.length; i++) {
			for (var j=0; j<2; j++) {
				var p = this._pixels[i][j];
				var pxVal = (j == 0) ? this.watermark_pos : val;
				var newPixel = this.getTamperedPixel([img.data[p], img.data[p+1], img.data[p+2]], pxVal);
				img.data[p] = newPixel[0];    // Red channel
				img.data[p+1] = newPixel[1];  // Green channel
				img.data[p+2] = newPixel[2];  // Blue channel
				//img.data[p+3] = 255;        // Alpha channel
			}
		}
		this.watermark_pos++;
		if (this.watermark_pos >= this.WATERMARK_LENGTH) this.watermark_pos = 0;
	},
	
	/**
	 * Get new pixel RGB from original pixel
	 * @param {int array} originalPixel
	 * @param {int} valueToInject
	 * @return {int array} tamperedPixel
	 */
	getTamperedPixel: function(px, value) {
		// Demo mode
		if (this.DEMO_MODE) return [255, 255, 255];
		
		// Create new pixel
		var newPx;
		
		// Find "x" (R+G+B+x%64=value)
		var x = [];
		var sum = px[0] + px[1] + px[2];
		for (var i=-63; i<=63; i++) {
			var res = (sum + i) % 64;
			if (res == value) {
				x.push(i);
			}
		}
		
		// Check if one solution is 0 ("perfect pixel")
		if (x.indexOf(0) > -1) return [px[0], px[1], px[2]];
		
		// Order "x" values
		if ((x.length > 1) && (Math.abs(x[1]) < Math.abs(x[0]))) x.reverse();
		
		// Try each "x" value
		for (var j=0; j<x.length; j++) {
			// Distribute "x" into R, B and G
			var k=0, div=3, newPx=[null, null, null], cachePx=[null, null, null], quotient = null, remainder = null, success = false;
			while (true) {
				if (quotient === null) {
					quotient = (x[j] > 0) ? Math.floor(x[j] / div) : Math.ceil(x[j] / div);
					remainder = x[j] % div;
				}
				if (k >= 3) {
					if (newPx[0] === null) newPx[0] = cachePx[0];
					if (newPx[1] === null) newPx[1] = cachePx[1];
					if (newPx[2] === null) newPx[2] = cachePx[2];
					success = true;
					break;
				} else if (newPx[k] === null) {
					cachePx[k] = px[k] + quotient + remainder;
					remainder = 0;
					if ((cachePx[k] < 0) || (cachePx[k] > 255)) {
						newPx[k] = px[k];
						div--;
						if (div <= 0) break;
						k = 0;
						quotient = null;
					} else {
						k++;
					}
				} else {
					k++;
				}
			}
			
			// Check for success
			if (success) break;
		}
		
		// Return tampered pixel
		return [newPx[0], newPx[1], newPx[2]];
	}
};