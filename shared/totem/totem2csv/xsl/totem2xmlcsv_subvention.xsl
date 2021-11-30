<?xml version="1.0" encoding="UTF-8"?>
<!--
Transform TOTEM xml Annexe Personnel file into CSV like XML file

TOTEM: http://odm-budgetaire.org/

author: Vincent Kober, Données et Cie Grenoble
-->
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:totem="http://www.minefi.gouv.fr/cp/demat/docbudgetaire">
  <xsl:output method="xml" encoding="utf-8" />
  
  <xsl:param name="plandecompte" />
        
  <!-- plandecompte path is given as parameter now -->
  <xsl:variable name="plan_de_compte" select="document(concat('../', $plandecompte))" />

    <xsl:template match="/">
    <xsl:variable name="NatDec">
    <xsl:variable name="code" select="//totem:BlocBudget/totem:NatDec/@V" />
      <!-- DecNat labels from CommunBudget.xsd -->
        <xsl:choose>
            <xsl:when test="$code = '01'">Budget primitif</xsl:when>
            <xsl:when test="$code = '02'">Décision modificative</xsl:when>
            <xsl:when test="$code = '03'">Budget supplémentaire</xsl:when>
            <xsl:when test="$code = '09'">Compte administratif</xsl:when>
            <xsl:otherwise>NatDec inconnu: <xsl:value-of select="$code"/></xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:variable name="Exer" select="//totem:BlocBudget/totem:Exer/@V" />
    <xsl:variable name="IdEtab" select="//totem:EnTeteBudget/totem:IdEtab/@V" />
    <xsl:variable name="LibelleColl" select="//totem:EnTeteDocBudgetaire/totem:LibelleColl/@V" />
        <csv>
            <header>
              <column name="nomAttribuant"/>
              <column name="idAttribuant"/>
              <column name="dateConvention"/>
              <column name="nomBeneficiaire"/>
              <column name="objet"/>
              <column name="montant"/>
              <column name="nature"/>  
              <column name="BGT_CodNatJurBenefCA"/>
              <column name="BGT_CodInvFonc"/>
              <column name="Budget"/>
            </header>
            <data>
                <xsl:for-each select=".//totem:CONCOURS">
                    <row lineno="{position()}">
                      <cell name="nomAttribuant" value="{$LibelleColl}" />
                      <cell name="idAttribuant" value="{$IdEtab}" />
                      <cell name="dateConvention" value="{$Exer}" />
                      <xsl:if test="totem:LibOrgaBenef">
                        <cell name="nomBeneficiaire" value="{totem:LibOrgaBenef/@V}" />
                      </xsl:if>
                      <xsl:if test="totem:ObjSubv">
                      <cell name="objet" value="{totem:ObjSubv/@V}" />
                      </xsl:if>
                      <xsl:if test="totem:MtSubv">
                        <cell name="montant" value="{totem:MtSubv/@V}" />
                      </xsl:if>
                      <xsl:variable name="nature" select="totem:CodArticle/@V" />
                      <cell name="nature">
                        <xsl:attribute name="value">
                            <xsl:value-of select="$plan_de_compte/Nomenclature/Nature/Comptes//Compte[@Code=$nature]/@Libelle" />
                        </xsl:attribute>
                    </cell>
                    <cell name="Budget" value="{$NatDec}" />
                    <xsl:if test="totem:CodNatJurBenefCA">
                          <xsl:variable name="NatJur">
                            <xsl:variable name="code" select="totem:CodNatJurBenefCA/@V" />
                            <!-- CodeNatJur labels from subventions.xsd -->
                              <xsl:choose>
                                <xsl:when test="$code = 'P1'">association</xsl:when>
                                <xsl:when test="$code = 'P2'">enterprise</xsl:when>
                                <xsl:when test="$code = 'P3'">personne physique</xsl:when>
                                <xsl:when test="$code = 'P4'">autre personne de droit privé</xsl:when>
                                <xsl:when test="$code = 'U1'">région</xsl:when>
                                <xsl:when test="$code = 'U2'">département</xsl:when>
                                <xsl:when test="$code = 'U3'">commune</xsl:when>
                                <xsl:when test="$code = 'U4'">établissement de droit public</xsl:when>
                                <xsl:when test="$code = 'U5'">état</xsl:when>
                                <xsl:when test="$code = 'U6'">autre personne de droit public</xsl:when>
                                <xsl:otherwise>Nature juridique inconnue: <xsl:value-of select="$code"/></xsl:otherwise>
                            </xsl:choose>
                        </xsl:variable>                         
                        <cell name="BGT_CodNatJurBenefCA" value="{$NatJur}" />
                        </xsl:if>
                        <xsl:if test="totem:CodInvFonc">                      
                          <cell name="BGT_CodInvFonc">
                            <xsl:variable name="section" select="totem:CodInvFonc/@V" />
                            <xsl:attribute name="value">
                                <xsl:if test="$section = 'I'">investissement</xsl:if>
                                <xsl:if test="$section = 'F'">fonctionnement</xsl:if>
                            </xsl:attribute>
                          </cell>
                        </xsl:if>  
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:CONCOURS">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
