#!/usr/bin/python

class templateError:
   def __init__(self, errorString):
      self.errorString = errorString
   def __repr__(self):
      return self.errorString
class templateDataError(templateError):
   pass
class templateDefinitionError(templateError):
   pass

import re
class templateParser:
   def __init__(self):
      self.replacements = []

   def parseTemplate(self, templateString, **kwargs):
      self.replacements.append(kwargs)

      # Remove any Delete sections
      templateString = re.compile(r"<!--StartDelete-->.*?<!--EndDelete-->", re.S).sub("", templateString)

      # Handle repeating templates first
      regEx = re.compile(r"<!--StartRepeat:(.*?)-->(.*?)<!--EndRepeat:\1-->", re.S)
      workingText = regEx.sub(self._handleListMatch, templateString)
      if "<!--StartRepeat" in workingText or "<!--EndRepeat" in workingText:
         raise templateDefinitionError(workingText)

      # handle all other single replacements
      workingText = self.parseSingleTemplate(workingText)
      self.replacements.pop()
      return workingText

   def parseSingleTemplate(self, templateString):
      # Handle conditional includes/deletes
      templateString = re.compile(r"<!--StartDeleteIf:(.*?)-->(.*?)<!--EndDeleteIf:\1-->", re.S).sub(self._handleDeleteIf, templateString)
      templateString = re.compile(r"<!--StartIncludeIf:(.*?)-->(.*?)<!--EndIncludeIf:\1-->", re.S).sub(self._handleIncludeIf, templateString)

      # Process any individual keywords
      result = re.compile("\^(.*?)\$").sub(self._replaceTemplateKeyword, templateString)
      return result

   def _handleListMatch(self, match):
      replacements = self.replacements[-1]
      listName = match.group(1)
      textToReplace = match.group(2).rstrip("\n")
      if not replacements.get(listName) and replacements.get(listName) != []: # allow empty dictionaries
         raise templateDataError(listName)
      entireResult = ""
      listToReplaceWith = replacements[listName]
      for listInList in listToReplaceWith[:-1]:
         entireResult = entireResult + self.parseTemplate(textToReplace, lastItem=False, **listInList)
      if len(listToReplaceWith) >= 1:
         entireResult = entireResult + self.parseTemplate(textToReplace, lastItem=True, **listToReplaceWith[-1])
      return entireResult.rstrip("\n").lstrip("\n")

   def _replaceTemplateKeyword(self, match):
      replacements = self.replacements[-1]
      matchText = match.group(1)
      if not matchText in replacements.keys():
         raise templateDataError(matchText)
      return replacements[matchText]

   def _handleDeleteIf(self, match):
      return self._handleConditionalInclude(match, False)

   def _handleIncludeIf(self, match):
      return self._handleConditionalInclude(match, True)

   def _handleConditionalInclude(self, match, includeIfTrue):
      replacements = self.replacements[-1]
      conditional = match.group(1)
      textToInclude = match.group(2).rstrip("\n")
      if (replacements[conditional] and includeIfTrue) or (not replacements[conditional] and not includeIfTrue):
         return textToInclude
      return ""

import unittest
class templateParsingTest(unittest.TestCase):
   def setUp(self):
      pass

   def tearDown(self):
      pass

   def testSingleReplace(self):
      template = "<a href=^linkUrl$>^linkText$</a>"
      parmsDict = {"linkUrl":"http://www.google.com", "linkText":"Google"}
      parser = templateParser()
      parseResult = parser.parseTemplate(template, **parmsDict)
      assert(parseResult == "<a href=http://www.google.com>Google</a>")

   def testDelete(self):
      template = """<!--StartDelete-->
      <a href=^linkUrl$>^linkText$</a>
      <!--EndDelete--><a href=^linkUrl$>^linkText$</a>"""
      parmsDict = {"linkUrl":"http://www.google.com", "linkText":"Google"}
      parser = templateParser()
      parseResult = parser.parseTemplate(template, **parmsDict)
      assert(parseResult == "<a href=http://www.google.com>Google</a>")

   def testConditionalInclude(self):
      template = """<!--StartIncludeIf:include-->text<!--EndIncludeIf:include-->"""
      parmsDict = {"linkUrl":"http://www.google.com", "linkText":"Google"}
      assert(templateParser().parseTemplate(template, include=True) == "text")
      assert(templateParser().parseTemplate(template, include=False) == "")

      template = """<!--StartDeleteIf:include-->text<!--EndDeleteIf:include-->"""
      parmsDict = {"linkUrl":"http://www.google.com", "linkText":"Google"}
      assert(templateParser().parseTemplate(template, include=False) == "text")
      assert(templateParser().parseTemplate(template, include=True) == "")

   def testGoodListReplace(self):
      template = """<!--StartRepeat:links-->
<td><a href=^linkUrl$>^linkText$</a></td>
<!--EndRepeat:links-->"""
      linksArray = [{"linkUrl":"http://www.google.com", "linkText":"Google"}]
      linksArray.append({"linkUrl":"http://www.python.org", "linkText":"Python"})
      linksArray.append({"linkUrl":"http://www.python.org", "linkText":"$$Lots of money^^"})
      parser = templateParser()
      parseResult = parser.parseTemplate(template, links=linksArray)
      expectedResult = """<td><a href=http://www.google.com>Google</a></td>
<td><a href=http://www.python.org>Python</a></td>
<td><a href=http://www.python.org>$$Lots of money^^</a></td>"""
      assert(parseResult == expectedResult)
      linksArray = [{"linkUrl":"http://www.google.com", "linkText":"Google"}]
      parseResult = parser.parseTemplate(template, links=linksArray)
      expectedResult = """<td><a href=http://www.google.com>Google</a></td>"""
      assert(parseResult == expectedResult)

   def testRecursiveListReplace(self):
      template = """<!--StartRepeat:links--><td><!--StartRepeat:chars-->>^char$<<!--EndRepeat:chars--></td><!--EndRepeat:links-->"""
      innerData = { "chars" : [{"char":"char1"}, {"char":"char2"}]}
      linksArray = [ innerData ]
      parser = templateParser()
      parseResult = parser.parseTemplate(template, links=linksArray)
      expectedResult = """<td>>char1<>char2<</td>"""
      assert(parseResult == expectedResult)

   def testNonGreedyReplace(self):
      template = """<!--StartDeleteIf:linkUrl-->foo<!--EndDeleteIf:linkUrl-->should see me<!--StartDeleteIf:linkUrl-->bar<!--EndDeleteIf:linkUrl-->"""
      parmsDict = {"linkUrl":"http://www.google.com", "linkText":"Google"}
      parser = templateParser()
      parseResult = parser.parseTemplate(template, **parmsDict)
      assert(parseResult == "should see me")

   def testBadListNameReplace(self):
      template = """<!--StartRepeat:links--><td><a href=^linkUrl$>^linkText$</a></td><!--EndRepeat:links-->"""
      linksArray = [{"linkUrl":"http://www.google.com", "linkText":"Google"}]
      parmsDict = {"bogus":linksArray}
      try: templateParser().parseTemplate(template, **parmsDict)
      except templateDataError: pass
      else: assert(False)

   def testBadListContentsReplace(self):
      template = """<!--StartRepeat:links--><td><a href=^linkUrl$>^linkText$</a></td><!--EndRepeat:links-->"""
      linksArray = [{"linkText":"Google"}]
      parmsDict = {"links":linksArray}
      try: templateParser().parseTemplate(template, **parmsDict)
      except templateDataError: pass
      else: assert(False)

   def testBadTemplateReplace(self):
      template = "<!--StartRepeat:links--><td><a href=^linkUrl$>^linkText$</a></td><!--EndRepeat:bogus-->"
      try: templateParser().parseTemplate(template)
      except templateError: pass
      else: assert(False)

if __name__ == "__main__":
   import os
   print "Called as standalone program; running unit tests..."
   testSuite = unittest.makeSuite(templateParsingTest, 'test')
   testRunner = unittest.TextTestRunner()
   testRunner.run(testSuite)
