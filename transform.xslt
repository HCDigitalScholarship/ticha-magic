<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="xhtml"/>
  <xsl:param name="spellchoice" select="'orig'"/>
  <xsl:param name="abbrchoice" select="'abbr'"/>
  <xsl:param name="textname" select="''"/>

  <xsl:template match="/">
    <body>
      <xsl:apply-templates select=".//text"/>
    </body>
  </xsl:template>

  <!-- transform <head> -->
  <xsl:template match="head">
    <h4>
      <xsl:apply-templates/>
    </h4>
  </xsl:template>
  <!-- don't transform <head type='outline'> -->
  <xsl:template match="head[@type='outline']"></xsl:template>

  <!-- handle <choice> elements with the $spellchoice and $abbrchoice parameters -->
  <xsl:template match="orig">
    <xsl:if test="$spellchoice = 'orig'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>
  <xsl:template match="reg[@type='spacing']">
    <xsl:if test="$spellchoice = 'reg-spacing'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>
  <xsl:template match="reg[@type='spanish']">
    <xsl:if test="$spellchoice = 'reg-spanish'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>
  <xsl:template match="abbr">
    <xsl:if test="$abbrchoice = 'abbr'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>
  <xsl:template match="expan">
    <xsl:if test="$abbrchoice = 'expan'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>

  <!-- transform <p> -->
  <xsl:template match="p">
    <p>
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  <xsl:template match="p[@rend='center']">
    <p class="center">
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <!-- transform <lb> -->
  <xsl:template match="lb">
    <br/>
  </xsl:template>

  <!-- transform <fw> -->
  <xsl:template match="fw[@type='catch']|fw[@type='catchword']">
    <div class="catch">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  <xsl:template match="fw[@type='sig']">
    <div class="sig">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- transform <hi> -->
  <xsl:template match="hi[@rend='italic']|hi[@rend='italics']">
    <span class="italic">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- transform <foreign> -->
  <xsl:template match="foreign">
    <xsl:if test="$textname != 'arte'">
      <xsl:apply-templates/>
    </xsl:if>
    <!-- Arte-specific logic -->
    <xsl:if test="$textname = 'arte'">
      <mark class="trigger">
        <xsl:apply-templates/>
      </mark>
    </xsl:if>
  </xsl:template>
  <xsl:template match="foreign[@rend='italic']|foreign[@rend='italics']">
    <xsl:if test="$textname != 'arte'">
      <span class="italic">
        <xsl:apply-templates/>
      </span>
    </xsl:if>
    <!-- Arte-specific logic -->
    <xsl:if test="$textname = 'arte'">
      <mark class="trigger">
        <span class="italic">
          <xsl:apply-templates/>
        </span>
      </mark>
    </xsl:if>
  </xsl:template>

  <!-- preserve these -->
  <xsl:template match="pb|cb|div">
    <!-- courtesy of stackoverflow.com/questions/26999058/, copies the div attributes -->
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
  <xsl:template match="cb">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
    </xsl:copy>
  </xsl:template>

  <!-- ignore these tags but copy their contents -->
  <xsl:template match="pc|div[@xml:id]|i|fw|emph|u|hi|gap|text">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- catch unmatched nodes, courtesy of stackoverflow.com/questions/3360017/ -->
  <xsl:template match="*">
    <xsl:message>STYLESHEET WARNING: unmatched element <xsl:value-of select="name()"/></xsl:message>
    <xsl:apply-templates/>
  </xsl:template>
</xsl:stylesheet>
