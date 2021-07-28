<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0">
  <xsl:import href="base.xslt" />
  <xsl:output omit-xml-declaration="yes" method="xhtml" indent="yes"/>
  <xsl:param name="spellchoice" select="'orig'"/>
  <xsl:param name="abbrchoice" select="'abbr'"/>

  <!-- Transform <foreign xml:lang="cvz"> so that we can do FLEx insertion. -->
  <xsl:template match="tei:foreign[@xml:lang='cvz']">
    <mark class="trigger">
      <xsl:apply-templates/>
    </mark>
  </xsl:template>

  <xsl:template match="tei:foreign[@rend='italic']|tei:foreign[@rend='italics']">
    <mark class="trigger">
      <span class="italic">
        <xsl:apply-templates/>
      </span>
    </mark>
  </xsl:template>

  <!-- don't ignore outline headers -->
  <xsl:template match="tei:head[@type='outline']">
    <h4 class="outline-header">
      <xsl:apply-templates/>
    </h4>
  </xsl:template>


</xsl:stylesheet>
