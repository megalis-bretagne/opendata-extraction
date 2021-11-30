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

    <xsl:template match="/">
        <xsl:variable name="NatDec" select="//totem:BlocBudget/totem:NatDec/@V" />
        <xsl:variable name="Exer" select="//totem:BlocBudget/totem:Exer/@V" />
        <xsl:variable name="IdEtab" select="//totem:EnTeteBudget/totem:IdEtab/@V" />
        <xsl:variable name="LibelleColl" select="//totem:EnTeteDocBudgetaire/totem:LibelleColl/@V" />
        <csv>
            <header>
                <column name="BGT_NATDEC"/>
                <column name="BGT_ANNEE"/>
                <column name="BGT_SIRET"/>
                <column name="BGT_NOM"/>
                <column name="CodVariPatrim"/>
                <column name="CodEntreeSorti"/>
                <column name="CodModalAcqui"/>
                <column name="LibBien"/>
                <column name="MtValAcquiBien"/>
                <column name="MtCumulAmortBien"/>
                <column name="MtAmortExer"/>
                <column name="DureeAmortBien"/>
                <column name="NumInventaire"/>
                <column name="DtAcquiBien"/>
                <column name="MtVNCBien3112"/>
                <column name="MtVNCBienSorti"/>
                <column name="MtPrixCessBienSorti"/>
            </header>
            <data>
                <xsl:for-each select=".//totem:PATRIMOINE">
                    <row lineno="{position()}">
                        <cell name="BGT_NATDEC" value="{$NatDec}" />
                        <cell name="BGT_ANNEE" value="{$Exer}" />
                        <cell name="BGT_SIRET" value="{$IdEtab}" />
                        <cell name="BGT_NOM" value="{$LibelleColl}" />
                        <xsl:if test="totem:BGT_NATDEC">
                          <cell name="BGT_NATDEC" value="{totem:BGT_NATDEC/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:BGT_ANNEE">
                          <cell name="BGT_ANNEE" value="{totem:BGT_ANNEE/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:BGT_SIRET">
                          <cell name="BGT_SIRET" value="{totem:BGT_SIRET/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:BGT_NOM">
                          <cell name="BGT_NOM" value="{totem:BGT_NOM/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodVariPatrim">
                          <cell name="CodVariPatrim" value="{totem:CodVariPatrim/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodEntreeSorti">
                          <cell name="CodEntreeSorti" value="{totem:CodEntreeSorti/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:CodModalAcqui">
                          <cell name="CodModalAcqui" value="{totem:CodModalAcqui/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:LibBien">
                          <cell name="LibBien" value="{totem:LibBien/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtValAcquiBien">
                          <cell name="MtValAcquiBien" value="{totem:MtValAcquiBien/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtCumulAmortBien">
                          <cell name="MtCumulAmortBien" value="{totem:MtCumulAmortBien/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtAmortExer">
                          <cell name="MtAmortExer" value="{totem:MtAmortExer/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:DureeAmortBien">
                          <cell name="DureeAmortBien" value="{totem:DureeAmortBien/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:NumInventaire">
                          <cell name="NumInventaire" value="{totem:NumInventaire/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:DtAcquiBien">
                          <cell name="DtAcquiBien" value="{totem:DtAcquiBien/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtVNCBien3112">
                          <cell name="MtVNCBien3112" value="{totem:MtVNCBien3112/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtVNCBienSorti">
                          <cell name="MtVNCBienSorti" value="{totem:MtVNCBienSorti/@V}" />
                        </xsl:if>
                        <xsl:if test="totem:MtPrixCessBienSorti">
                          <cell name="MtPrixCessBienSorti" value="{totem:MtPrixCessBienSorti/@V}" />
                        </xsl:if>
                    </row>
                </xsl:for-each>
            </data>
        </csv>
    </xsl:template>

    <xsl:template match="totem:PATRIMOINE">
        <xsl:copy-of select="."/>
    </xsl:template>

</xsl:stylesheet>
