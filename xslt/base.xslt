<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:tei="http://www.tei-c.org/ns/1.0">
  <xsl:output omit-xml-declaration="yes" method="xhtml" indent="yes"/>
  <xsl:param name="spellchoice" select="'orig'"/>
  <xsl:param name="abbrchoice" select="'abbr'"/>


  <xsl:template match="/">
    <body>
      <xsl:apply-templates select="tei:TEI/tei:text" />
    </body>
  </xsl:template>


  <!-- Transform <head> -->
  <xsl:template match="tei:head">
    <h4>
      <xsl:apply-templates/>
    </h4>
  </xsl:template>


  <!-- Handle <choice> elements with the $spellchoice and $abbrchoice parameters -->
  <xsl:template match="tei:orig">
    <xsl:if test="$spellchoice = 'orig'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:reg[@type='spacing']">
    <xsl:if test="$spellchoice = 'reg-spacing'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:reg[@type='spanish']">
    <xsl:if test="$spellchoice = 'reg-spanish'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:reg">
    <xsl:if test="$spellchoice != 'orig'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:abbr">
    <xsl:if test="$abbrchoice = 'abbr'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>

  <xsl:template match="tei:expan">
    <xsl:if test="$abbrchoice = 'expan'">
      <xsl:apply-templates/>
    </xsl:if>
  </xsl:template>


  <!-- Transform <p> -->
  <xsl:template match="tei:p">
    <p>
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <xsl:template match="tei:p[@rend='center']">
    <p class="center">
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <!-- Transform <lb> -->
  <xsl:template match="tei:lb">
    <br/>
  </xsl:template>


  <!-- Transform <fw> -->
  <xsl:template match="tei:fw[@type='catch']|tei:fw[@type='catchword']">
    <div class="catch">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <xsl:template match="tei:fw[@type='sig']">
    <div class="sig">
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <!-- Transform <hi> -->
  <xsl:template match="tei:hi[@rend='italic']|tei:hi[@rend='italics']">
    <span class="italic">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <!-- Transform <foreign> -->
  <xsl:template match="tei:foreign[@rend='italic']|tei:foreign[@rend='italics']">
    <span class="italic">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <!-- Preserve these (without the TEI namespace) -->
  <xsl:template match="tei:del|tei:cb|tei:pb|tei:div">
    <xsl:element name="{local-name()}">
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <!-- Eliminate the namespace on xml:id -->
  <xsl:template match="tei:div[@xml:id]">
    <div>
      <xsl:attribute name="id">
        <xsl:value-of select="@xml:id" />
      </xsl:attribute>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  <xsl:template match="tei:del[@xml:id]">
    <del>
      <xsl:attribute name="id">
        <xsl:value-of select="@xml:id" />
      </xsl:attribute>
      <xsl:copy-of select="@*[local-name() != 'id']"/>
      <xsl:apply-templates/>
    </del>
  </xsl:template>


  <!-- Ignore these but copy their contents -->
  <xsl:template match="tei:pc|tei:i|tei:fw|tei:emph|tei:u|tei:hi|tei:gap|tei:text|tei:choice|tei:ref|tei:front|tei:body|tei:back|tei:g|tei:c|tei:add|tei:foreign">
    <xsl:apply-templates/>
  </xsl:template>


  <!-- Ignore these and their contents -->
  <xsl:template match="tei:head[@type='outline']">
  </xsl:template>


  <!-- Catch unmatched nodes, courtesy of stackoverflow.com/questions/3360017/ -->
  <xsl:template match="*">
    <xsl:message>STYLESHEET WARNING: unmatched element <xsl:value-of select="name()"/></xsl:message>
    <xsl:apply-templates/>
  </xsl:template>
</xsl:stylesheet>
