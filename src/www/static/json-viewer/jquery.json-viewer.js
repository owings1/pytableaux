/**
 * jQuery json-viewer
 * @author: Alexandre Bodelot <alexandre.bodelot@gmail.com>
 * @link: https://github.com/abodelot/jquery.json-viewer
 *
 * =========================================================
 *  
 * Modifications by Doug Owings <doug@dougowings.net>.
 *
 * 2022-03-21
 * ----------
 *    * Use URL interface for validting URLs. IE requires polyfill.
 *    * Fix major security/escaping bugs.
 *    * Replace deprecated `.click()` with `.trigger('click')`.
 *    * Use `href="javascript:"` for placeholder instead of `return false`.
 *    * Type checking changes with isArray, isObject.
 *    * Various housekeeping.
 *    * Added the following classes:
 *      - json-number   : in addition to existing json-literal class
 *      - json-boolean  : in addition to existing json-literal class
 *      - json-null     : in addition to existing json-literal class
 *      - json-obrace   : around object (curly) braces '{' and '}'
 *      - json-abrace   : around array (corner) braces '[' and ']'
 *      - json-comma    : around ','
 *      - json-colon    : around ':'
 *      - json-key      : around every key, in addition to existing json-string
 *                        class when options.withQuotes is enabled.
 */
(function($) {

  /**
   * Check if arg is an array.
   * @return boolean
   */
  function isArray(arg) {
    return Object.prototype.toString.call(arg) === '[object Array]';
  }

  /**
   * Check if arg is an object.
   * @return boolean
   */
  function isObject(arg) {
    return Object.prototype.toString.call(arg) === '[object Object]';
  }

  /**
   * Check if obj has own property key.
   * @return boolean
   */
  function hasOwnKey(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  }

  /**
   * Check if arg is either an array with at least 1 element, or a dict with at least 1 key
   * @return boolean
   */
  function isCollapsable(arg) {
    if (isArray(arg)) {
      return Boolean(arg.length);
    }
    if (!isObject(arg)) {
      return false;
    }
    for (var _ in arg) {
      return true;
    }
    return false;
  }

  /**
   * Check if val is a valid URL, respecting any plugin options.
   * @return boolean
   */
  function isUrl(val, options) {
    try {
      return Boolean(new URL(val))
    } catch (e) {
      return false
    }
  }
  /**
   * Escape using encodeURIComponent.
   * 
   * @param {string} str The input string.
   * @return {string} Escaped output.
   */
  function esc(str) {
    return encodeURIComponent(str);
  }

  /**
   * Transform a json object into html representation
   * @return {string}
   */
  function json2html(json, options) {
    var html = '';
    var $build;
    var valtype = typeof json;
    if (valtype === 'string') {
      if (options.withLinks && isUrl(json, options)) {
        $build = $('<a class="json-string" target="_blank"/>').text(json).attr('href', json)
      } else {
        // JSON.stringify will add outer double-quotes and escape inner double-quotes.
        json = JSON.stringify(json)
        $build = $('<span class="json-string"/>').text(json)
      }
      html += $build.get(0).outerHTML;
    } else if (valtype === 'number') {
      // Escape URI chars as a safeguard.
      html += '<span class="json-literal json-number">' + esc(json) + '</span>';
    } else if (valtype === 'boolean') {
      html += '<span class="json-literal json-boolean">' + json + '</span>';
    } else if (json === null) {
      html += '<span class="json-literal json-null">null</span>';
    } else if (isArray(json)) {
      if (json.length > 0) {
        html += '<span class="json-abrace">[</span><ol class="json-array">';
        for (var i = 0; i < json.length; ++i) {
          html += '<li>';
          // Add toggle button if item is collapsable
          if (isCollapsable(json[i])) {
            html += '<a href="javascript:" class="json-toggle"></a>';
          }
          html += json2html(json[i], options);
          // Add comma if item is not last
          if (i < json.length - 1) {
            html += '<span class="json-comma">,</span>';
          }
          html += '</li>';
        }
        html += '</ol><span class="json-abrace">]</span>';
      } else {
        html += '<span class="json-abrace">[]</span>';
      }
    } else if (valtype === 'object') {
      var keys = Object.keys(json);
      var keyCount = keys.length;
      if (keyCount > 0) {
        html += '<span class="json-obrace">{</span><ul class="json-dict">';
        for (var key in json) {
          if (hasOwnKey(json, key)) {
            html += '<li>';
            $build = $('<span class="json-key"/>');
            if (options.withQuotes) {
              $build.addClass('json-string');
              // JSON.stringify will add outer double-quotes and escape inner double-quotes.
              $build.text(JSON.stringify(key));
            } else {
              $build.text(key);
            }
            var keyRepr = $build.get(0).outerHTML;

            // Add toggle button if item is collapsable
            if (isCollapsable(json[key])) {
              html += '<a href="javascript:" class="json-toggle">' + keyRepr + '</a>';
            } else {
              html += keyRepr;
            }
            html += '<span class="json-colon">:</span> ' + json2html(json[key], options);
            // Add comma if item is not last
            if (--keyCount > 0) {
              html += '<span class="json-comma">,</span>';
            }
            html += '</li>';
          }
        }
        html += '</ul><span class="json-obrace">}</span>';
      } else {
        html += '<span class="json-obrace">{}</span>';
      }
    }
    return html;
  }

  /**
   * jQuery plugin method
   * @param json: a javascript object
   * @param options: an optional options hash
   */
  $.fn.jsonViewer = function(json, options) {
    // Merge user options with default options
    options = Object.assign({}, {
      collapsed: false,
      rootCollapsable: true,
      withQuotes: false,
      withLinks: true,
    }, options);

    // jQuery chaining
    return this.each(function() {

      // Transform to HTML
      var html = json2html(json, options);
      if (options.rootCollapsable && isCollapsable(json)) {
        html = '<a href="javascript:" class="json-toggle"></a>' + html;
      }

      var $me = $(this)
      // Insert HTML in target DOM element
      $me.html(html);
      $me.addClass('json-document');

      // Bind click on toggle buttons
      $me.off('click');
      $me.on('click', 'a.json-toggle', function() {
        var target = $(this).toggleClass('collapsed').siblings('ul.json-dict, ol.json-array');
        target.toggle();
        if (target.is(':visible')) {
          target.siblings('.json-placeholder').remove();
        } else {
          var count = target.children('li').length;
          var placeholder = count + (count > 1 ? ' items' : ' item');
          target.after('<a href="javascript:" class="json-placeholder">' + placeholder + '</a>');
        }
      });

      // Simulate click on toggle button when placeholder is clicked
      $me.on('click', 'a.json-placeholder', function() {
        $(this).siblings('a.json-toggle').trigger('click');
      });

      if (options.collapsed == true) {
        // Trigger click to collapse all nodes
        $me.find('a.json-toggle').trigger('click');
      }
    });
  };
})(jQuery);
